"""Extrae los literales traducibles y genera/actualiza el .po.

Sustituto de `makemessages` para este entorno, donde no hay xgettext ni
permisos para instalarlo. Recorre plantillas y .py buscando {% translate %},
{% blocktranslate %} y _(...), y conserva las traducciones ya escritas.
"""
import re
import sys
import pathlib
import polib

ROOT = pathlib.Path(__file__).resolve().parents[2]

RE_TRANS = re.compile(r'\{%\s*translate\s+"((?:[^"\\]|\\.)*)"\s*%\}')
RE_TRANS_SQ = re.compile(r"\{%\s*translate\s+'((?:[^'\\]|\\.)*)'\s*%\}")
RE_BLOCK = re.compile(r'\{%\s*blocktranslate(?:\s+[^%]*?)?\s*%\}(.*?)\{%\s*endblocktranslate\s*%\}', re.S)
RE_PLURAL = re.compile(r'\{%\s*plural\s*%\}')
RE_PY = re.compile(r'_\(\s*((?:"(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\')(?:\s*\n?\s*(?:"(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\'))*)\s*\)')


def py_literal(raw):
    try:
        return eval(raw, {'__builtins__': {}}, {})
    except Exception:
        return None


def django_msgid(body):
    # Django escapa los % literales a %% porque el mensaje se interpola con
    # formato de %; las variables {{ x }} pasan a ser %(x)s.
    out = []
    for i, chunk in enumerate(re.split(r'(\{\{\s*[\w.]+\s*\}\})', body)):
        if i % 2:
            out.append('%%(%s)s' % chunk.strip('{} ').strip())
        else:
            out.append(chunk.replace('%', '%%'))
    return ''.join(out)


plurals = {}


def collect():
    found = {}   # msgid -> set de "fichero:linea"

    def add(msgid, where, strip=True):
        # Los literales de Python van tal cual: un \n al principio o al final
        # forma parte del msgid y recortarlo rompería la búsqueda en runtime.
        if strip:
            msgid = msgid.strip()
        if msgid.strip():
            found.setdefault(msgid, set()).add(where)

    for path in sorted(ROOT.rglob('*.html')):
        if '.venv' in path.parts or 'staticfiles' in path.parts:
            continue
        text = path.read_text()
        rel = path.relative_to(ROOT)
        for regex in (RE_TRANS, RE_TRANS_SQ):
            for m in regex.finditer(text):
                # Django duplica los % del msgid también en {% translate %}
                # (Variable.resolve lo hace antes de buscar en el catálogo) y
                # los deshace al renderizar, así que van escapados.
                lit = m.group(1).replace('\\"', '"').replace("\\'", "'")
                add(lit.replace('%', '%%'),
                    f'{rel}:{text[:m.start()].count(chr(10)) + 1}')
        for m in RE_BLOCK.finditer(text):
            body = m.group(1)
            line = text[:m.start()].count(chr(10)) + 1
            # Django construye el msgid con el contenido literal y convierte
            # {{ var }} en %(var)s. Ni se recorta ni se colapsan espacios.
            parts = [django_msgid(x) for x in RE_PLURAL.split(body)]
            if len(parts) == 2:
                plurals.setdefault(parts[0], parts[1])
            for part in parts:
                add(part, f'{rel}:{line}', strip=False)

    # ast en vez de regex: capta los literales implícitamente concatenados
    # en varias líneas, como el cuerpo del email de confirmación.
    import ast
    for path in sorted(ROOT.rglob('*.py')):
        if any(x in path.parts for x in ('.venv', 'migrations', 'staticfiles')):
            continue
        rel = path.relative_to(ROOT)
        try:
            tree = ast.parse(path.read_text())
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                    and node.func.id == '_' and len(node.args) == 1
                    and isinstance(node.args[0], ast.Constant)
                    and isinstance(node.args[0].value, str)):
                add(node.args[0].value, f'{rel}:{node.lineno}', strip=False)
    return found


def main(lang):
    po_path = ROOT / 'locale' / lang / 'LC_MESSAGES' / 'django.po'
    po_path.parent.mkdir(parents=True, exist_ok=True)

    existing = {}
    if po_path.exists():
        for entry in polib.pofile(str(po_path)):
            if entry.msgstr:
                existing[entry.msgid] = entry.msgstr

    po = polib.POFile(wrapwidth=0)
    po.metadata = {
        'Project-Id-Version': 'EuroPeptiva',
        'Language': lang,
        'MIME-Version': '1.0',
        'Content-Type': 'text/plain; charset=UTF-8',
        'Content-Transfer-Encoding': '8bit',
        'Plural-Forms': 'nplurals=2; plural=(n != 1);',
    }

    found = collect()
    skip = set(plurals.values())
    for msgid in sorted(found):
        if msgid in skip:
            continue
        occ = [(o.split(':')[0], o.split(':')[1]) for o in sorted(found[msgid])]
        if msgid in plurals:
            pl = plurals[msgid]
            po.append(polib.POEntry(
                msgid=msgid, msgid_plural=pl, occurrences=occ,
                msgstr_plural={0: existing.get(msgid, ''), 1: existing.get(pl, '')},
            ))
        else:
            po.append(polib.POEntry(
                msgid=msgid, msgstr=existing.get(msgid, ''), occurrences=occ))
    po.save(str(po_path))
    total = len(po)
    done = sum(1 for e in po if e.msgstr)
    print(f'{po_path.relative_to(ROOT)}: {total} literales, {done} traducidos, {total - done} pendientes')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'en')

"""Rellena el `research_background` de los 18 productos, en español e inglés.

Reglas que sigue el texto, por si hay que ampliarlo:

- Qué es la molécula y qué se ha estudiado de ella. Nada de eficacia, dosis,
  pautas ni uso humano.
- Se dice de dónde viene la evidencia. Si es preclínica (BPC-157, TB-500,
  MOTS-c, los blends), se dice; si la literatura procede casi toda de un solo
  país (Semax, Selank), también. Distinguir "estudiado en roedores" de "con
  ensayos clínicos amplios" es lo que impide que la ficha se lea como una
  promesa.
- Los dos blends no tienen literatura propia: lo publicado va de cada
  componente por separado, y el texto lo dice en lugar de sugerir lo contrario.

Se indexa por slug y no por PK: producción y local no tienen por qué coincidir.
"""

from django.db import migrations

CONTEXTO = {
    'retatrutide': (
        "Retatrutide es un péptido sintético diseñado para activar a la vez tres receptores del "
        "metabolismo: el de GLP-1, el de GIP y el de glucagón. La hipótesis que se investiga es "
        "que cada uno aporta algo distinto —control del apetito, señalización de la insulina y "
        "gasto energético— y que combinarlos en una sola molécula produce un efecto que ninguno "
        "alcanza por separado.\n\n"
        "Es una molécula reciente. La literatura disponible procede sobre todo de ensayos "
        "publicados a partir de 2023 en investigación sobre obesidad y diabetes tipo 2, más "
        "trabajo preclínico sobre señalización de receptores acoplados a proteína G. Sigue en "
        "desarrollo, así que su cuerpo de evidencia es mucho menor que el de los agonistas GLP-1 "
        "clásicos.",

        "Retatrutide is a synthetic peptide designed to activate three metabolic receptors at "
        "once: those for GLP-1, GIP and glucagon. The hypothesis under investigation is that each "
        "contributes something different — appetite control, insulin signaling and energy "
        "expenditure — and that combining them in a single molecule produces an effect none of "
        "them reaches alone.\n\n"
        "It is a recent molecule. The available literature comes mainly from trials published "
        "from 2023 onwards in obesity and type 2 diabetes research, plus preclinical work on "
        "G protein-coupled receptor signaling. It is still in development, so its body of "
        "evidence is far smaller than that of the classic GLP-1 agonists.",
    ),
    'semaglutide': (
        "La semaglutida es un análogo del péptido GLP-1 humano modificado en dos puntos: una "
        "sustitución que lo protege de la degradación por la enzima DPP-4 y una cadena de ácido "
        "graso que lo une a la albúmina del plasma. Esas dos modificaciones son lo que alarga su "
        "vida media de minutos a días.\n\n"
        "Es de los péptidos metabólicos con más literatura detrás: programas de ensayos clínicos "
        "amplios sobre control glucémico y peso corporal, más trabajo preclínico sobre los "
        "receptores GLP-1 del páncreas, el hipotálamo y el tracto digestivo. En investigación se "
        "emplea a menudo como comparador frente al que medir moléculas nuevas.",

        "Semaglutide is an analog of the human GLP-1 peptide modified at two points: a "
        "substitution that protects it from degradation by the DPP-4 enzyme, and a fatty acid "
        "chain that binds it to plasma albumin. Those two modifications are what stretch its "
        "half-life from minutes to days.\n\n"
        "It is among the metabolic peptides with the most literature behind them: large clinical "
        "trial programs on glycemic control and body weight, plus preclinical work on the GLP-1 "
        "receptors of the pancreas, the hypothalamus and the digestive tract. In research it is "
        "often used as the comparator against which new molecules are measured.",
    ),
    'bpc-157': (
        "BPC-157 es un pentadecapéptido —quince aminoácidos— cuya secuencia procede de un "
        "fragmento de una proteína protectora del jugo gástrico humano. A diferencia de muchos "
        "péptidos de investigación es estable en medio ácido, y ahí empieza buena parte del "
        "interés que despierta.\n\n"
        "La literatura es casi toda preclínica: modelos animales de lesión de tendón, ligamento, "
        "músculo y mucosa digestiva, con líneas de trabajo sobre angiogénesis por la vía del "
        "VEGFR2 y sobre su interacción con el sistema del óxido nítrico. Conviene subrayarlo "
        "porque es la clave para interpretar el resto: no hay ensayos clínicos amplios que "
        "respalden esos hallazgos en humanos. Es una molécula muy estudiada en roedores y muy "
        "poco estudiada fuera de ellos.",

        "BPC-157 is a pentadecapeptide — fifteen amino acids — whose sequence comes from a "
        "fragment of a protective protein found in human gastric juice. Unlike many research "
        "peptides it is stable in acidic conditions, and that is where much of the interest in it "
        "begins.\n\n"
        "The literature is almost entirely preclinical: animal models of tendon, ligament, muscle "
        "and gut mucosa injury, with lines of work on angiogenesis through the VEGFR2 pathway and "
        "on its interaction with the nitric oxide system. This is worth stressing because it is "
        "the key to reading everything else: there are no large clinical trials backing those "
        "findings in humans. It is a molecule studied a great deal in rodents and very little "
        "outside them.",
    ),
    'tb-500': (
        "TB-500 es la versión sintética del fragmento activo de la timosina beta-4, una proteína "
        "de 43 aminoácidos presente en casi todos los tejidos. El fragmento corresponde a la "
        "región que se une a la actina, donde reside buena parte de su actividad biológica.\n\n"
        "Lo que se investiga gira alrededor de la dinámica del citoesqueleto: la timosina beta-4 "
        "secuestra actina monomérica y con ello influye en la migración celular, un paso "
        "necesario tanto en la reparación de tejidos como en la formación de vasos nuevos. Hay "
        "trabajo en modelos de lesión cardíaca, corneal y cutánea, todo preclínico o en fases "
        "clínicas tempranas.",

        "TB-500 is the synthetic version of the active fragment of thymosin beta-4, a 43 amino "
        "acid protein present in almost every tissue. The fragment corresponds to the "
        "actin-binding region, where much of its biological activity resides.\n\n"
        "What is being investigated revolves around cytoskeletal dynamics: thymosin beta-4 "
        "sequesters monomeric actin and thereby influences cell migration, a step required both "
        "in tissue repair and in the formation of new blood vessels. There is work in models of "
        "cardiac, corneal and skin injury, all of it preclinical or in early clinical phases.",
    ),
    'bac-water': (
        "El agua bacteriostática no es un principio activo: es agua para inyección con un 0,9 % "
        "de alcohol bencílico añadido como conservante. Ese conservante es lo que la separa del "
        "agua estéril corriente y lo que permite perforar el mismo vial varias veces sin que "
        "prolifere nada en su interior.\n\n"
        "En el trabajo con péptidos liofilizados es el disolvente estándar precisamente por eso: "
        "un vial rara vez se agota en una sola extracción. Merece la pena tener presente que el "
        "alcohol bencílico no es inerte para todos los ensayos ni compatible con todos los "
        "preparados, así que el disolvente se elige en función del diseño experimental y no por "
        "costumbre.",

        "Bacteriostatic water is not an active compound: it is water for injection with 0.9% "
        "benzyl alcohol added as a preservative. That preservative is what sets it apart from "
        "plain sterile water, and what allows the same vial to be pierced several times without "
        "anything growing inside it.\n\n"
        "In work with lyophilized peptides it is the standard solvent for exactly that reason: a "
        "vial is rarely used up in a single withdrawal. It is worth keeping in mind that benzyl "
        "alcohol is not inert for every assay, nor compatible with every preparation, so the "
        "solvent should be chosen to suit the experimental design rather than out of habit.",
    ),
    'ghk-cu': (
        "El GHK es un tripéptido —glicina, histidina y lisina— que aparece de forma natural en el "
        "plasma humano y que tiene una afinidad muy alta por el cobre(II). El complejo que forma "
        "con ese ion es la forma en la que se estudia. Su concentración en plasma disminuye con "
        "la edad, y ese dato es el que abrió la línea de investigación.\n\n"
        "Lo estudiado se concentra en la matriz extracelular: síntesis de colágeno y elastina, "
        "remodelado tisular y modulación de la expresión génica en fibroblastos, con trabajo "
        "adicional sobre el folículo piloso. Buena parte de la literatura es de cultivo celular y "
        "de modelos animales; en dermatología hay estudios en humanos, pero de tamaño pequeño.",

        "GHK is a tripeptide — glycine, histidine and lysine — that occurs naturally in human "
        "plasma and has a very high affinity for copper(II). The complex it forms with that ion is "
        "the form in which it is studied. Its plasma concentration declines with age, and that "
        "observation is what opened the line of research.\n\n"
        "What has been studied centers on the extracellular matrix: collagen and elastin "
        "synthesis, tissue remodeling and modulation of gene expression in fibroblasts, with "
        "further work on the hair follicle. Much of the literature is cell culture and animal "
        "models; in dermatology there are human studies, but small ones.",
    ),
    'melanotan-1': (
        "Melanotan I es un análogo sintético de la hormona α-MSH con dos sustituciones que lo "
        "hacen mucho más resistente a la degradación que la hormona natural. Actúa sobre el "
        "receptor MC1R, que es el que gobierna la producción de eumelanina en el melanocito.\n\n"
        "La línea de investigación principal ha sido la fotoprotección: aumentar la eumelanina de "
        "la piel sin mediar exposición a radiación ultravioleta. Su desarrollo clínico se dirigió "
        "a una porfiria poco frecuente en la que los pacientes no toleran la luz, y ahí es donde "
        "se concentra la evidencia más sólida. La selectividad por MC1R es lo que lo separa de "
        "Melanotan II.",

        "Melanotan I is a synthetic analog of the α-MSH hormone carrying two substitutions that "
        "make it far more resistant to degradation than the natural hormone. It acts on the MC1R "
        "receptor, which governs eumelanin production in the melanocyte.\n\n"
        "The main line of research has been photoprotection: increasing the skin's eumelanin "
        "without ultraviolet exposure. Its clinical development targeted a rare porphyria in "
        "which patients cannot tolerate light, and that is where the most solid evidence sits. "
        "Selectivity for MC1R is what separates it from Melanotan II.",
    ),
    'melanotan-2': (
        "Melanotan II es un análogo cíclico de la α-MSH. La ciclación lo estabiliza, pero también "
        "le quita selectividad: en lugar de actuar casi solo sobre MC1R como Melanotan I, activa "
        "además los receptores MC3R, MC4R y MC5R.\n\n"
        "Eso ensancha lo que se investiga. MC1R lleva a la pigmentación; MC4R está implicado en la "
        "regulación del apetito y del balance energético y en la respuesta sexual —de esta "
        "molécula derivó de hecho otro péptido desarrollado específicamente para esa vía—. La "
        "contrapartida de la falta de selectividad es que los efectos fuera del objetivo son más "
        "frecuentes, y es un punto que aparece de forma recurrente en la literatura.",

        "Melanotan II is a cyclic analog of α-MSH. Cyclization stabilizes it, but it also costs it "
        "selectivity: instead of acting almost solely on MC1R as Melanotan I does, it also "
        "activates the MC3R, MC4R and MC5R receptors.\n\n"
        "That widens what is being investigated. MC1R leads to pigmentation; MC4R is involved in "
        "appetite and energy balance regulation and in sexual response — another peptide "
        "developed specifically for that pathway in fact derives from this molecule. The flip "
        "side of that lack of selectivity is that off-target effects are more frequent, a point "
        "that comes up repeatedly in the literature.",
    ),
    'tesamorelin': (
        "La tesamorelina es un análogo de la GHRH, la hormona que ordena a la hipófisis liberar "
        "hormona del crecimiento. Lleva una modificación en el extremo N que la protege de la "
        "degradación por DPP-4, lo que alarga su acción respecto a la GHRH natural.\n\n"
        "Su interés en investigación está en que actúa río arriba: en lugar de introducir hormona "
        "del crecimiento desde fuera, estimula la que produce el propio organismo y conserva el "
        "patrón pulsátil de secreción. La línea con más datos es la del tejido adiposo visceral y "
        "el eje GH/IGF-1, con trabajo clínico en lipodistrofia asociada a la infección por VIH.",

        "Tesamorelin is an analog of GHRH, the hormone that tells the pituitary to release growth "
        "hormone. It carries an N-terminal modification that protects it from DPP-4 degradation, "
        "extending its action compared with natural GHRH.\n\n"
        "Its research interest lies in acting upstream: instead of introducing growth hormone from "
        "outside, it stimulates what the body produces itself and preserves the pulsatile pattern "
        "of secretion. The line with the most data is visceral adipose tissue and the GH/IGF-1 "
        "axis, with clinical work in lipodystrophy associated with HIV infection.",
    ),
    'semax': (
        "Semax es un heptapéptido derivado de la ACTH: reproduce el fragmento 4-7 de esa hormona y "
        "le añade una cola de tres aminoácidos (Pro-Gly-Pro) que lo protege de las peptidasas. Ese "
        "fragmento carece de la actividad hormonal de la ACTH completa, lo que permite estudiar "
        "sus efectos sobre el sistema nervioso por separado.\n\n"
        "La investigación se ha centrado en la expresión de factores neurotróficos —BDNF y NGF "
        "sobre todo—, en la neuroprotección en modelos de isquemia y en cognición. Importa saber "
        "de dónde viene esa literatura: la molécula se desarrolló en Rusia y la mayor parte de los "
        "estudios están publicados allí, con poca replicación independiente fuera.",

        "Semax is a heptapeptide derived from ACTH: it reproduces the 4-7 fragment of that hormone "
        "and adds a three amino acid tail (Pro-Gly-Pro) that protects it from peptidases. The "
        "fragment lacks the hormonal activity of full ACTH, which makes it possible to study its "
        "effects on the nervous system in isolation.\n\n"
        "Research has centered on the expression of neurotrophic factors — BDNF and NGF above all "
        "— on neuroprotection in ischemia models, and on cognition. It matters where that "
        "literature comes from: the molecule was developed in Russia and most studies are "
        "published there, with little independent replication elsewhere.",
    ),
    'selank': (
        "Selank es un heptapéptido construido sobre la tuftsina, un tetrapéptido del sistema "
        "inmune, al que se añade la misma cola Pro-Gly-Pro que estabiliza a Semax frente a las "
        "peptidasas.\n\n"
        "Lo estudiado es sobre todo su efecto ansiolítico en modelos animales, y los mecanismos "
        "que se le atribuyen pasan por la modulación de los sistemas GABAérgico y serotoninérgico "
        "y por cambios en la expresión de BDNF; hay además trabajo sobre su vertiente "
        "inmunomoduladora, herencia de la tuftsina. Comparte con Semax la misma limitación de "
        "fondo: se desarrolló en Rusia y la literatura publicada fuera de ese ámbito es escasa.",

        "Selank is a heptapeptide built on tuftsin, a tetrapeptide of the immune system, with the "
        "same Pro-Gly-Pro tail added that stabilizes Semax against peptidases.\n\n"
        "What has been studied is above all its anxiolytic effect in animal models, and the "
        "mechanisms attributed to it run through modulation of the GABAergic and serotonergic "
        "systems and through changes in BDNF expression; there is also work on its "
        "immunomodulatory side, inherited from tuftsin. It shares the same underlying limitation "
        "as Semax: it was developed in Russia and the literature published outside that sphere is "
        "sparse.",
    ),
    'tirzepatide': (
        "La tirzepatida es un péptido de agonismo dual: activa a la vez el receptor de GLP-1 y el "
        "de GIP. Está construida sobre el esqueleto del GIP y lleva una cadena de ácido graso que "
        "la une a la albúmina, lo que le da una vida media larga.\n\n"
        "Lo interesante en investigación es que el papel del GIP en el metabolismo no está "
        "cerrado: hay trabajo que sostiene que agonizar ese receptor y trabajo que sostiene que "
        "antagonizarlo producen efectos parecidos sobre el peso corporal, y la tirzepatida es la "
        "herramienta con la que se estudia esa paradoja. Tiene detrás programas clínicos amplios "
        "en diabetes tipo 2 y obesidad.",

        "Tirzepatide is a dual agonist peptide: it activates the GLP-1 and the GIP receptor at the "
        "same time. It is built on the GIP backbone and carries a fatty acid chain binding it to "
        "albumin, which gives it a long half-life.\n\n"
        "What makes it interesting in research is that GIP's role in metabolism is not settled: "
        "there is work arguing that agonizing that receptor and work arguing that antagonizing it "
        "produce similar effects on body weight, and tirzepatide is the tool used to study that "
        "paradox. It has large clinical programs behind it in type 2 diabetes and obesity.",
    ),
    'mots-c': (
        "MOTS-c es uno de los pocos péptidos que no están codificados en el ADN del núcleo: su "
        "secuencia de dieciséis aminoácidos está dentro del gen del ARN ribosómico 12S del genoma "
        "mitocondrial. Pertenece a la familia de los péptidos derivados de la mitocondria, "
        "descrita hace poco más de una década.\n\n"
        "Se investiga como señal que la mitocondria envía al resto de la célula y al núcleo. Las "
        "líneas principales son la activación de AMPK, la interferencia con el ciclo del folato y "
        "la metionina, y su papel en la homeostasis metabólica y en la respuesta al ejercicio. Los "
        "niveles circulantes descienden con la edad, y de ahí viene el interés desde la biología "
        "del envejecimiento. La evidencia disponible es preclínica.",

        "MOTS-c is one of the few peptides not encoded in nuclear DNA: its sixteen amino acid "
        "sequence sits inside the 12S ribosomal RNA gene of the mitochondrial genome. It belongs "
        "to the family of mitochondria-derived peptides, described only a little over a decade "
        "ago.\n\n"
        "It is investigated as a signal the mitochondrion sends to the rest of the cell and to the "
        "nucleus. The main lines are AMPK activation, interference with the folate and methionine "
        "cycle, and its role in metabolic homeostasis and the response to exercise. Circulating "
        "levels decline with age, which is where the interest from aging biology comes from. The "
        "available evidence is preclinical.",
    ),
    'wolverine-blend': (
        "Wolverine Blend no es una molécula nueva: es la coformulación en un mismo vial de TB-500 "
        "y BPC-157, los dos péptidos con más literatura preclínica en reparación de tejidos.\n\n"
        "El motivo para juntarlos es que actúan por vías distintas —TB-500 sobre la dinámica de la "
        "actina y la migración celular, BPC-157 sobre la angiogénesis y la señalización del óxido "
        "nítrico—, lo que hace razonable preguntarse por un efecto combinado. Conviene ser claro "
        "en un punto: la literatura existente estudia cada péptido por separado y los datos sobre "
        "la combinación son escasos. Es precisamente lo que queda por investigar.",

        "Wolverine Blend is not a new molecule: it is the co-formulation in a single vial of "
        "TB-500 and BPC-157, the two peptides with the most preclinical literature in tissue "
        "repair.\n\n"
        "The reason for combining them is that they act through different pathways — TB-500 on "
        "actin dynamics and cell migration, BPC-157 on angiogenesis and nitric oxide signaling — "
        "which makes a combined effect a reasonable question to ask. One point should be clear: "
        "the existing literature studies each peptide separately, and data on the combination is "
        "sparse. That is precisely what remains to be investigated.",
    ),
    'glow70-blend': (
        "Glow70 Blend reúne en un solo vial tres péptidos con líneas de investigación en biología "
        "cutánea: GHK-Cu, Melanotan I y BPC-157.\n\n"
        "Cada uno entra por un lado distinto de la piel. El GHK-Cu se estudia en la matriz "
        "extracelular y la síntesis de colágeno; Melanotan I, en la producción de eumelanina a "
        "través del receptor MC1R; BPC-157, en angiogénesis y reparación tisular. La combinación "
        "no tiene literatura propia: lo publicado se refiere a cada componente por separado, y "
        "estudiar cómo interactúan entre sí es justamente el objeto de una preparación como esta.",

        "Glow70 Blend brings together in a single vial three peptides with research lines in skin "
        "biology: GHK-Cu, Melanotan I and BPC-157.\n\n"
        "Each one enters the skin from a different side. GHK-Cu is studied in the extracellular "
        "matrix and collagen synthesis; Melanotan I, in eumelanin production through the MC1R "
        "receptor; BPC-157, in angiogenesis and tissue repair. The combination has no literature "
        "of its own: what is published refers to each component separately, and studying how they "
        "interact is exactly the point of a preparation like this one.",
    ),
    'igf-1-lr3': (
        "IGF-1 LR3 es un análogo del factor de crecimiento insulínico tipo 1 con dos cambios: una "
        "sustitución en la posición 3 y una extensión de trece aminoácidos en el extremo N. Ambos "
        "reducen su afinidad por las proteínas transportadoras (IGFBP), que en el organismo "
        "secuestran a la mayor parte del IGF-1 circulante.\n\n"
        "Esa es la razón de su uso: al circular libre dura más y resulta bastante más potente que "
        "el IGF-1 nativo en cultivo. De hecho es un reactivo habitual en medios de cultivo celular "
        "y en bioprocesos industriales, donde se emplea para sostener la proliferación de líneas "
        "celulares. En investigación se estudia sobre la vía IGF-1R/PI3K/Akt, en crecimiento "
        "celular y en reparación de tejido muscular.",

        "IGF-1 LR3 is an analog of insulin-like growth factor 1 with two changes: a substitution "
        "at position 3 and a thirteen amino acid extension at the N-terminus. Both reduce its "
        "affinity for the binding proteins (IGFBPs), which in the body sequester most of the "
        "circulating IGF-1.\n\n"
        "That is the reason it is used: circulating free, it lasts longer and is considerably more "
        "potent than native IGF-1 in culture. It is in fact a routine reagent in cell culture "
        "media and industrial bioprocessing, where it is used to sustain the proliferation of cell "
        "lines. In research it is studied around the IGF-1R/PI3K/Akt pathway, in cell growth and "
        "in muscle tissue repair.",
    ),
    'glutation': (
        "El glutatión es un tripéptido de glutamato, cisteína y glicina con una peculiaridad "
        "estructural: el enlace del glutamato es gamma y no alfa, lo que lo hace resistente a las "
        "peptidasas corrientes. Es el antioxidante no proteico más abundante de la célula.\n\n"
        "Lo que se estudia de él es el equilibrio redox: la proporción entre su forma reducida "
        "(GSH) y su forma oxidada (GSSG) se usa como indicador del estrés oxidativo de una célula. "
        "Participa además en la conjugación de fase II a través de las glutatión-S-transferasas y "
        "es el cofactor de las glutatión-peroxidasas. Un punto recurrente en la literatura es su "
        "mala biodisponibilidad por vía oral, que es lo que ha dirigido la investigación hacia "
        "otras rutas y hacia sus precursores.",

        "Glutathione is a tripeptide of glutamate, cysteine and glycine with a structural quirk: "
        "the glutamate bond is gamma rather than alpha, which makes it resistant to ordinary "
        "peptidases. It is the most abundant non-protein antioxidant in the cell.\n\n"
        "What is studied about it is redox balance: the ratio between its reduced form (GSH) and "
        "its oxidized form (GSSG) is used as an indicator of a cell's oxidative stress. It also "
        "takes part in phase II conjugation through the glutathione S-transferases and is the "
        "cofactor of the glutathione peroxidases. A recurring point in the literature is its poor "
        "oral bioavailability, which is what has pushed research towards other routes and towards "
        "its precursors.",
    ),
    'nad-plus': (
        "El NAD+ no es un péptido sino una coenzima de nucleótidos, presente en todas las células. "
        "Cumple dos papeles distintos: transportador de electrones en la glucólisis, el ciclo de "
        "Krebs y la fosforilación oxidativa, y sustrato que se consume en reacciones de "
        "señalización.\n\n"
        "El segundo es el que ha abierto la línea de investigación actual. Las sirtuinas, las PARP "
        "implicadas en la reparación del ADN y la CD38 consumen NAD+, y sus niveles descienden con "
        "la edad. De ahí el trabajo sobre biosíntesis y precursores —nicotinamida ribósido y "
        "mononucleótido—, sobre la relación entre metabolismo energético y envejecimiento celular, "
        "y sobre la reparación del ADN.",

        "NAD+ is not a peptide but a nucleotide coenzyme, present in every cell. It plays two "
        "distinct roles: electron carrier in glycolysis, the Krebs cycle and oxidative "
        "phosphorylation, and substrate consumed in signaling reactions.\n\n"
        "The second is what opened the current line of research. The sirtuins, the PARPs involved "
        "in DNA repair and CD38 all consume NAD+, and its levels decline with age. Hence the work "
        "on biosynthesis and precursors — nicotinamide riboside and mononucleotide — on the "
        "relationship between energy metabolism and cellular aging, and on DNA repair.",
    ),
}


def rellenar(apps, schema_editor):
    Peptide = apps.get_model('store', 'Peptide')
    for peptide in Peptide.objects.all():
        textos = CONTEXTO.get(peptide.slug)
        if not textos:
            continue
        es, en = textos
        peptide.research_background = es
        peptide.research_background_es = es
        peptide.research_background_en = en
        peptide.save(update_fields=[
            'research_background', 'research_background_es', 'research_background_en',
        ])


def vaciar(apps, schema_editor):
    apps.get_model('store', 'Peptide').objects.update(
        research_background='', research_background_es='', research_background_en='',
    )


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0009_formato_y_descripcion_sin_conservacion'),
    ]

    operations = [
        migrations.RunPython(rellenar, vaciar),
    ]

#!/bin/bash
# Ejecutar en el VPS como root DESPUÉS de clonar el repo
# Uso: bash /home/peptidos/app/deploy/setup_server.sh
set -e

APP_DIR="/home/peptidos/app"
USER="peptidos"

echo "=== [1/6] Entorno Python ==="
cd $APP_DIR
sudo -u $USER python3 -m venv venv
sudo -u $USER venv/bin/pip install --upgrade pip -q
sudo -u $USER venv/bin/pip install -r requirements.txt -q
sudo -u $USER venv/bin/pip install psycopg2-binary gunicorn -q
echo "OK"

echo "=== [2/6] Archivo .env ==="
if [ ! -f "$APP_DIR/.env" ]; then
    echo "ERROR: Falta el archivo .env en $APP_DIR"
    echo "Crea /home/peptidos/app/.env con las variables de producción antes de continuar."
    exit 1
fi
echo "OK"

echo "=== [3/6] Migraciones y estáticos ==="
sudo -u $USER bash -c "cd $APP_DIR && venv/bin/python manage.py migrate --noinput"
sudo -u $USER bash -c "cd $APP_DIR && venv/bin/python manage.py collectstatic --noinput --clear -v 0"
sudo -u $USER bash -c "cd $APP_DIR && venv/bin/python manage.py loaddata store/fixtures/initial_products.json" || echo "Fixtures ya cargadas, OK"
echo "OK"

echo "=== [4/6] Superusuario admin ==="
sudo -u $USER bash -c "cd $APP_DIR && venv/bin/python manage.py shell -c \"
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'pepepablopaco@gmail.com', 'CAMBIAR_PASSWORD_ADMIN')
    print('Superusuario creado: admin / CAMBIAR_PASSWORD_ADMIN')
else:
    print('Superusuario ya existe')
\""

echo "=== [5/6] Servicio systemd ==="
cp $APP_DIR/deploy/europeptiva.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable europeptiva
systemctl start europeptiva
sleep 2
systemctl is-active europeptiva && echo "Servicio activo OK" || echo "ERROR: revisar con: journalctl -u europeptiva -n 30"

echo "=== [6/6] Nginx ==="
cp $APP_DIR/deploy/nginx.conf /etc/nginx/sites-available/europeptiva
ln -sf /etc/nginx/sites-available/europeptiva /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx && echo "Nginx OK"

echo ""
echo "========================================"
echo "Setup completado."
echo ""
echo "PRÓXIMOS PASOS:"
echo "1. Cambia la contraseña del admin:"
echo "   sudo -u peptidos bash -c 'cd /home/peptidos/app && venv/bin/python manage.py changepassword admin'"
echo ""
echo "2. SSL con Certbot (cuando el DNS esté propagado):"
echo "   certbot --nginx -d europeptiva.com -d www.europeptiva.com -d europeptiva.es -d www.europeptiva.es --non-interactive --agree-tos --email pepepablopaco@gmail.com --redirect"
echo ""
echo "3. Verifica la web en: http://167.233.169.95"
echo "========================================"

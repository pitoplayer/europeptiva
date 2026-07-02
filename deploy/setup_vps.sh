#!/bin/bash
# Script de configuración inicial del VPS Hetzner
# Ejecutar como root después de crear el VPS
# Uso: bash setup_vps.sh

set -e

echo "=== Configurando VPS para EuroPeptiva ==="

# 1. Actualizar sistema
apt update && apt upgrade -y

# 2. Instalar dependencias
apt install -y \
    python3.11 python3.11-venv python3-pip \
    postgresql postgresql-contrib \
    nginx certbot python3-certbot-nginx \
    git curl ufw

# 3. Crear usuario de aplicación
useradd -m -s /bin/bash peptidos || true
mkdir -p /home/peptidos/logs

# 4. Configurar PostgreSQL
sudo -u postgres psql << 'PSQL'
CREATE USER europeptiva WITH PASSWORD 'CAMBIAR_ESTA_PASSWORD';
CREATE DATABASE europeptiva OWNER europeptiva;
GRANT ALL PRIVILEGES ON DATABASE europeptiva TO europeptiva;
\q
PSQL

# 5. Configurar firewall
ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw --force enable

# 6. Clonar repositorio
sudo -u peptidos bash << 'BASH'
cd /home/peptidos
git clone https://github.com/pitoplayer/europeptiva.git app
cd app
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Crear .env
cat > /home/peptidos/app/.env << 'ENV'
SECRET_KEY=GENERAR_CON_python_-c_"import_secrets;_print(secrets.token_urlsafe(50))"
DEBUG=False
ALLOWED_HOSTS=europeptiva.com,www.europeptiva.com,europeptiva.es
DATABASE_URL=postgres://europeptiva:CAMBIAR_ESTA_PASSWORD@localhost/europeptiva
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
DEFAULT_FROM_EMAIL=EuroPeptiva <noreply@europeptiva.com>
ADMIN_EMAIL=pepepablopaco@gmail.com
BANK_IBAN=
BANK_HOLDER=
ENV

python manage.py migrate
python manage.py collectstatic --noinput
python manage.py loaddata store/fixtures/initial_products.json
BASH

# 7. Instalar servicio systemd
cp /home/peptidos/app/deploy/europeptiva.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable europeptiva
systemctl start europeptiva

# 8. Configurar Nginx
cp /home/peptidos/app/deploy/nginx.conf /etc/nginx/sites-available/europeptiva
ln -sf /etc/nginx/sites-available/europeptiva /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx

# 9. SSL con Certbot
certbot --nginx -d europeptiva.com -d www.europeptiva.com -d europeptiva.es -d www.europeptiva.es \
    --non-interactive --agree-tos --email pepepablopaco@gmail.com --redirect

echo ""
echo "=== Setup completado ==="
echo "IMPORTANTE: Edita /home/peptidos/app/.env con los valores reales"
echo "Luego: systemctl restart europeptiva"
echo ""
echo "Crea el superadmin con:"
echo "  sudo -u peptidos bash -c 'cd /home/peptidos/app && source venv/bin/activate && python manage.py createsuperuser'"

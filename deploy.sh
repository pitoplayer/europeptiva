#!/bin/bash
# Deploy a producción en Hetzner VPS
# Uso: ./deploy.sh [IP_DEL_VPS]
# Ejemplo: ./deploy.sh 1.2.3.4

set -e

VPS_IP="${1:-}"
VPS_USER="peptidos"
APP_DIR="/home/peptidos/app"

if [ -z "$VPS_IP" ]; then
    echo "Uso: ./deploy.sh <IP_DEL_VPS>"
    exit 1
fi

echo "🚀 Desplegando EuroPeptiva en $VPS_IP..."

# Push local changes first
git add -A
git diff --cached --quiet || git commit -m "deploy: $(date +'%Y-%m-%d %H:%M')"
git push

# Deploy en el servidor
ssh "$VPS_USER@$VPS_IP" << 'ENDSSH'
    set -e
    cd /home/peptidos/app
    echo "📥 Actualizando código..."
    git pull origin main

    echo "📦 Instalando dependencias..."
    source venv/bin/activate
    pip install -r requirements.txt --quiet

    echo "🗃️  Aplicando migraciones..."
    python manage.py migrate --noinput

    echo "📁 Recolectando estáticos..."
    python manage.py collectstatic --noinput --clear

    echo "🔄 Reiniciando servicios..."
    sudo systemctl restart europeptiva
    sudo systemctl reload nginx

    echo "✅ Deploy completado."
    python manage.py check --deploy 2>&1 | head -20
ENDSSH

echo ""
echo "✅ EuroPeptiva actualizado en https://europeptiva.com"

#!/bin/bash

# 🚀 Script de despliegue completo para data.arrebolweddings.com
# Ejecutar desde tu máquina local: ./deploy-remote.sh IP_DEL_SERVIDOR

SERVER_IP=$1
SSH_KEY="$HOME/.ssh/id_ed25519_digitalocean"
DOMAIN="data.arrebolweddings.com"

if [ -z "$SERVER_IP" ]; then
    echo "❌ Error: Proporciona la IP del servidor"
    echo "📖 Uso: ./deploy-remote.sh IP_DEL_SERVIDOR"
    exit 1
fi

echo "🚀 Iniciando despliegue de Baserow en $DOMAIN"
echo "🎯 Servidor: $SERVER_IP"

# 1. Subir archivos al servidor
echo "📤 Subiendo archivos..."
scp -i "$SSH_KEY" baserow-deploy.tar.gz root@$SERVER_IP:/opt/
if [ $? -ne 0 ]; then
    echo "❌ Error subiendo archivos. Verifica la conexión SSH."
    exit 1
fi

# 2. Ejecutar despliegue remoto
echo "🔧 Ejecutando despliegue en el servidor..."
ssh -i "$SSH_KEY" root@$SERVER_IP << 'ENDSSH'
    set -e
    
    echo "📦 Extrayendo archivos..."
    cd /opt
    tar -xzf baserow-deploy.tar.gz
    
    echo "🔧 Actualizando sistema..."
    apt update && apt upgrade -y
    
    echo "📦 Instalando dependencias..."
    apt install -y docker.io docker-compose nginx certbot python3-certbot-nginx ufw
    
    echo "🐳 Iniciando Docker..."
    systemctl enable docker
    systemctl start docker
    
    echo "🔒 Configurando firewall..."
    ufw --force reset
    ufw allow OpenSSH
    ufw allow 'Nginx Full'
    ufw --force enable
    
    echo "🌐 Configurando Nginx..."
    cp nginx-baserow.conf /etc/nginx/sites-available/baserow
    ln -sf /etc/nginx/sites-available/baserow /etc/nginx/sites-enabled/
    rm -f /etc/nginx/sites-enabled/default
    nginx -t && systemctl reload nginx
    
    echo "🔐 Configurando SSL..."
    certbot --nginx -d data.arrebolweddings.com --non-interactive --agree-tos --email admin@arrebolweddings.com --redirect
    
    echo "⚙️ Configurando variables de entorno..."
    cp .env.production .env
    
    # Generar claves seguras
    SECRET_KEY=$(openssl rand -base64 64 | tr -d "=+/" | cut -c1-64)
    DB_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-32)
    REDIS_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-32)
    
    sed -i "s/CAMBIAR_POR_CLAVE_SEGURA_ALEATORIA_64_CARACTERES/${SECRET_KEY}/" .env
    sed -i "s/CAMBIAR_POR_PASSWORD_SEGURO_DB/${DB_PASSWORD}/" .env
    sed -i "s/CAMBIAR_POR_PASSWORD_SEGURO_REDIS/${REDIS_PASSWORD}/" .env
    
    echo "🐳 Desplegando Baserow..."
    docker-compose -f docker-compose.production.yml up -d
    
    echo "⏳ Esperando inicialización..."
    sleep 30
    
    echo "✅ ¡Despliegue completado!"
    echo "🌐 Baserow disponible en: https://data.arrebolweddings.com"
    echo "📊 Estado del contenedor:"
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    
ENDSSH

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 ¡DESPLIEGUE EXITOSO!"
    echo "🌐 Tu Baserow está disponible en: https://data.arrebolweddings.com"
    echo "⏳ Espera 1-2 minutos para que se inicialice completamente"
    echo ""
    echo "📋 Próximos pasos:"
    echo "1. Configura DNS: data.arrebolweddings.com → $SERVER_IP"
    echo "2. Visita https://data.arrebolweddings.com"
    echo "3. Crea tu cuenta de administrador"
    echo ""
    echo "🔧 Comandos útiles:"
    echo "ssh -i $SSH_KEY root@$SERVER_IP 'docker logs baserow_production'"
    echo "ssh -i $SSH_KEY root@$SERVER_IP 'docker-compose -f /opt/docker-compose.production.yml restart'"
else
    echo "❌ Error durante el despliegue. Revisa los logs."
fi
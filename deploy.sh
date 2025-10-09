#!/bin/bash

# Script de despliegue para Baserow en DigitalOcean
# Configurado para data.arrebolweddings.com

SUBDOMINIO="data"
DOMAIN="data.arrebolweddings.com"

echo "🚀 Desplegando Baserow en ${DOMAIN}"

# 1. Actualizar sistema
echo "📦 Actualizando sistema..."
sudo apt update && sudo apt upgrade -y

# 2. Instalar dependencias
echo "🔧 Instalando dependencias..."
sudo apt install -y docker.io docker-compose nginx certbot python3-certbot-nginx ufw

# 3. Configurar firewall
echo "🔒 Configurando firewall..."
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw --force enable

# 4. Configurar Nginx
echo "🌐 Configurando Nginx..."
sudo cp nginx-baserow.conf /etc/nginx/sites-available/baserow
sudo ln -sf /etc/nginx/sites-available/baserow /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx

# 5. Obtener certificado SSL
echo "🔐 Configurando SSL con Let's Encrypt..."
sudo certbot --nginx -d ${DOMAIN} --non-interactive --agree-tos --email admin@arrebolweddings.com

# 6. Configurar variables de entorno
echo "⚙️ Configurando variables de entorno..."
cp .env.production .env

# Generar claves seguras
SECRET_KEY=$(openssl rand -base64 64 | tr -d "=+/" | cut -c1-64)
DB_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-32)
REDIS_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-32)

sed -i "s/CAMBIAR_POR_CLAVE_SEGURA_ALEATORIA_64_CARACTERES/${SECRET_KEY}/" .env
sed -i "s/CAMBIAR_POR_PASSWORD_SEGURO_DB/${DB_PASSWORD}/" .env
sed -i "s/CAMBIAR_POR_PASSWORD_SEGURO_REDIS/${REDIS_PASSWORD}/" .env

# 7. Desplegar Baserow
echo "🐳 Desplegando Baserow..."
sudo docker-compose -f docker-compose.production.yml up -d

echo "✅ ¡Despliegue completado!"
echo "🌐 Tu Baserow está disponible en: https://${DOMAIN}"
echo "⏳ Espera 1-2 minutos para que se inicialice completamente"
echo ""
echo "📝 Pasos finales:"
echo "1. Visita https://${DOMAIN}"
echo "2. Crea tu cuenta de administrador"
echo "3. ¡Comienza a usar Baserow!"
# 🔐 Script PowerShell para despliegue remoto en DigitalOcean

param(
    [Parameter(Mandatory=$true)]
    [string]$ServerIP,
    
    [Parameter(Mandatory=$false)]
    [string]$SSHKey = "$env:USERPROFILE\.ssh\id_ed25519_digitalocean"
)

$Domain = "data.arrebolweddings.com"

Write-Host "🚀 Iniciando despliegue de Baserow en $Domain" -ForegroundColor Green
Write-Host "🎯 Servidor: $ServerIP" -ForegroundColor Cyan
Write-Host "🔑 Clave SSH: $SSHKey" -ForegroundColor Yellow

# 1. Verificar archivos necesarios
if (-not (Test-Path "baserow-deploy.tar.gz")) {
    Write-Host "❌ Error: baserow-deploy.tar.gz no encontrado" -ForegroundColor Red
    Write-Host "💡 Ejecuta primero: tar -czf baserow-deploy.tar.gz .env.production docker-compose.production.yml nginx-baserow.conf deploy.sh README_DEPLOY.md" -ForegroundColor Yellow
    exit 1
}

# 2. Subir archivos
Write-Host "📤 Subiendo archivos al servidor..." -ForegroundColor Blue
$scpCmd = "scp -i `"$SSHKey`" baserow-deploy.tar.gz root@${ServerIP}:/opt/"
Write-Host "Ejecutando: $scpCmd" -ForegroundColor Gray
Invoke-Expression $scpCmd

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Error subiendo archivos. Verifica la conexión SSH." -ForegroundColor Red
    exit 1
}

# 3. Crear script de despliegue remoto
$remoteScript = @"
#!/bin/bash
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
certbot --nginx -d $Domain --non-interactive --agree-tos --email admin@arrebolweddings.com --redirect

echo "⚙️ Configurando variables de entorno..."
cp .env.production .env

# Generar claves seguras
SECRET_KEY=`$(openssl rand -base64 64 | tr -d "=+/" | cut -c1-64)
DB_PASSWORD=`$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-32)
REDIS_PASSWORD=`$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-32)

sed -i "s/CAMBIAR_POR_CLAVE_SEGURA_ALEATORIA_64_CARACTERES/`${SECRET_KEY}/" .env
sed -i "s/CAMBIAR_POR_PASSWORD_SEGURO_DB/`${DB_PASSWORD}/" .env
sed -i "s/CAMBIAR_POR_PASSWORD_SEGURO_REDIS/`${REDIS_PASSWORD}/" .env

echo "🐳 Desplegando Baserow..."
docker-compose -f docker-compose.production.yml up -d

echo "⏳ Esperando inicialización..."
sleep 30

echo "✅ ¡Despliegue completado!"
echo "🌐 Baserow disponible en: https://$Domain"
echo "📊 Estado del contenedor:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
"@

# 4. Ejecutar en el servidor
Write-Host "🔧 Ejecutando despliegue en el servidor..." -ForegroundColor Blue
$sshCmd = "ssh -i `"$SSHKey`" root@$ServerIP `"$remoteScript`""
Write-Host "Conectando al servidor..." -ForegroundColor Gray

# Crear archivo temporal para el script
$tempScript = New-TemporaryFile
$remoteScript | Out-File -FilePath $tempScript.FullName -Encoding UTF8

# Subir y ejecutar script
scp -i "$SSHKey" $tempScript.FullName "root@${ServerIP}:/opt/deploy-script.sh"
ssh -i "$SSHKey" root@$ServerIP "chmod +x /opt/deploy-script.sh && /opt/deploy-script.sh"

# Limpiar archivo temporal
Remove-Item $tempScript.FullName

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "🎉 ¡DESPLIEGUE EXITOSO!" -ForegroundColor Green
    Write-Host "🌐 Tu Baserow está disponible en: https://$Domain" -ForegroundColor Cyan
    Write-Host "⏳ Espera 1-2 minutos para que se inicialice completamente" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "📋 Próximos pasos:" -ForegroundColor Blue
    Write-Host "1. Configura DNS: $Domain → $ServerIP" -ForegroundColor White
    Write-Host "2. Visita https://$Domain" -ForegroundColor White
    Write-Host "3. Crea tu cuenta de administrador" -ForegroundColor White
    Write-Host ""
    Write-Host "🔧 Comandos útiles:" -ForegroundColor Blue
    Write-Host "ssh -i `"$SSHKey`" root@$ServerIP 'docker logs baserow_production'" -ForegroundColor Gray
    Write-Host "ssh -i `"$SSHKey`" root@$ServerIP 'docker-compose -f /opt/docker-compose.production.yml restart'" -ForegroundColor Gray
} else {
    Write-Host "❌ Error durante el despliegue. Revisa los logs." -ForegroundColor Red
}
"@

$PowerShellScript | Out-File -FilePath "C:\WWW\Baserow\Deploy-Baserow.ps1" -Encoding UTF8
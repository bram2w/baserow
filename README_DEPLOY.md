# 🚀 Baserow para data.arrebolweddings.com

## ✅ Configuración Completada
Tu Baserow está configurado para: **https://data.arrebolweddings.com**

## 📦 Pasos de Despliegue

### 1. Subir archivos al servidor DigitalOcean
```bash
# Desde tu máquina local (PowerShell/CMD)
scp -r C:\WWW\Baserow root@TU-SERVER-IP:/opt/baserow
```

### 2. Conectar al servidor y desplegar
```bash
# SSH al servidor
ssh root@TU-SERVER-IP

# Ir al directorio
cd /opt/baserow

# Hacer ejecutable el script
chmod +x deploy.sh

# Ejecutar despliegue automático
./deploy.sh
```

### 3. Configurar DNS
En tu panel de DNS (DigitalOcean, Cloudflare, etc.):
- **Tipo:** A
- **Nombre:** data
- **Valor:** IP de tu servidor
- **TTL:** 300 (5 minutos)

## ⏱️ Tiempo de despliegue
- **Script automático:** ~5-10 minutos
- **Propagación DNS:** ~5-30 minutos
- **Inicialización Baserow:** ~2-3 minutos

## 🎯 Resultado Final
- **URL:** https://data.arrebolweddings.com
- **SSL:** Automático con Let's Encrypt
- **Seguridad:** Firewall + Headers configurados
- **Backup:** Datos persistentes en volumen Docker

## 📧 Configuración de Email (Opcional)
Edita `.env` en el servidor para configurar SMTP:
```bash
EMAIL_SMTP_USER=noreply@arrebolweddings.com
EMAIL_SMTP_PASSWORD=tu-password-smtp
```

## 🛠️ Comandos Útiles Post-Despliegue
```bash
# Ver logs
sudo docker logs baserow_production

# Reiniciar
sudo docker-compose -f docker-compose.production.yml restart

# Actualizar
sudo docker-compose -f docker-compose.production.yml pull
sudo docker-compose -f docker-compose.production.yml up -d

# Backup manual
sudo docker exec baserow_production baserow backup
```

## ✨ ¡Todo listo!
Después del despliegue, visita https://data.arrebolweddings.com y crea tu cuenta de administrador.
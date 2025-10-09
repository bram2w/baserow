# Guía de Despliegue de Baserow en DigitalOcean

## 🎯 Objetivo
Desplegar Baserow en tu servidor DigitalOcean bajo un subdominio de arrebolweddings.com

## 📋 Requisitos
- Servidor DigitalOcean con Ubuntu 20.04+ 
- Dominio arrebolweddings.com configurado
- Acceso SSH al servidor

## 🚀 Pasos de Despliegue

### 1. Subir archivos al servidor
```bash
# En tu máquina local
scp -r C:\WWW\Baserow root@tu-servidor-ip:/opt/baserow
```

### 2. Conectarse al servidor
```bash
ssh root@tu-servidor-ip
cd /opt/baserow
```

### 3. Elegir subdominio y ejecutar despliegue
```bash
# Hacer el script ejecutable
chmod +x deploy.sh

# Ejecutar con el subdominio que prefieras
./deploy.sh baserow    # Para baserow.arrebolweddings.com
# o
./deploy.sh datos      # Para datos.arrebolweddings.com
# o  
./deploy.sh admin      # Para admin.arrebolweddings.com
```

### 4. Configurar DNS
En tu panel de DigitalOcean o proveedor de DNS:
- Crear registro A: `SUBDOMINIO.arrebolweddings.com` → IP del servidor

## ⚙️ Configuración Manual (si prefieres)

### Variables de entorno importantes:
```bash
# Editar .env.production antes del despliegue
BASEROW_PUBLIC_URL=https://SUBDOMINIO.arrebolweddings.com
EMAIL_SMTP_USER=tu-email@arrebolweddings.com
EMAIL_SMTP_PASSWORD=tu-password-email
```

### Comandos útiles:
```bash
# Ver logs
sudo docker logs baserow_production

# Reiniciar servicio
sudo docker-compose -f docker-compose.production.yml restart

# Backup
sudo docker exec baserow_production baserow backup

# Actualizar
sudo docker-compose -f docker-compose.production.yml pull
sudo docker-compose -f docker-compose.production.yml up -d
```

## 🔒 Seguridad
- ✅ SSL automático con Let's Encrypt
- ✅ Firewall configurado (solo SSH, HTTP, HTTPS)
- ✅ Headers de seguridad en Nginx
- ✅ Claves generadas automáticamente

## 📧 Email
Configura tu SMTP en `.env`:
- Gmail, SendGrid, o tu proveedor preferido
- Necesario para invitaciones y recuperación de contraseñas

## 🎉 ¡Listo!
Tu Baserow estará disponible en `https://SUBDOMINIO.arrebolweddings.com`
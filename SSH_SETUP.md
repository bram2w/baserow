# 🔐 Configuración SSH para DigitalOcean

## ✅ Claves SSH Generadas
- **Clave privada:** `%USERPROFILE%\.ssh\id_ed25519_digitalocean`
- **Clave pública:** `%USERPROFILE%\.ssh\id_ed25519_digitalocean.pub`

## 📋 Tu Clave Pública SSH (Copiar esta línea completa):
```
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIEChVJCXq/Z720Iy8NTNVrlD4TL3vCPsdZTu457MJFG0 arrebolweddings-baserow-2025-10-08
```

## 🚀 Pasos para configurar DigitalOcean:

### 1. Agregar clave SSH en DigitalOcean:
1. Ve a [DigitalOcean Panel](https://cloud.digitalocean.com/account/security)
2. Clic en **"Add SSH Key"**
3. Pega la clave pública de arriba
4. Nombre: `ArrebolWeddings-Baserow-2025`

### 2. Crear Droplet con SSH:
1. **Create Droplet**
2. **OS:** Ubuntu 22.04 LTS
3. **Plan:** Basic ($6/mes mínimo recomendado)
4. **Región:** New York/San Francisco (más cerca de México)
5. **Authentication:** SSH Key (selecciona la que acabas de crear)
6. **Hostname:** `arrebol-baserow`

### 3. Conectar usando SSH:
```bash
# Conectar al servidor (reemplaza IP_DEL_SERVIDOR)
ssh -i %USERPROFILE%\.ssh\id_ed25519_digitalocean root@IP_DEL_SERVIDOR
```

### 4. Subir archivos de Baserow:
```bash
# Subir archivo comprimido
scp -i %USERPROFILE%\.ssh\id_ed25519_digitalocean C:\WWW\Baserow\baserow-deploy.tar.gz root@IP_DEL_SERVIDOR:/opt/

# O subir directorio completo
scp -r -i %USERPROFILE%\.ssh\id_ed25519_digitalocean C:\WWW\Baserow root@IP_DEL_SERVIDOR:/opt/
```

## 🔧 Configuración SSH automática (opcional):
Crear archivo: `%USERPROFILE%\.ssh\config`
```
Host arrebol-baserow
    HostName IP_DEL_SERVIDOR
    User root
    IdentityFile %USERPROFILE%\.ssh\id_ed25519_digitalocean
    IdentitiesOnly yes
```

Después podrás conectar simplemente con:
```bash
ssh arrebol-baserow
```

## 🛡️ Seguridad:
- ✅ Clave ED25519 (más segura que RSA)
- ✅ Sin contraseña (solo clave)
- ✅ Identificador único para este proyecto
- ✅ Acceso exclusivo desde tu máquina

## ⚡ Comandos Rápidos:
```bash
# Copiar clave pública al clipboard
Get-Content "$env:USERPROFILE\.ssh\id_ed25519_digitalocean.pub" | clip

# Probar conexión SSH
ssh -i %USERPROFILE%\.ssh\id_ed25519_digitalocean -o ConnectTimeout=10 root@IP_DEL_SERVIDOR

# Desplegar Baserow directamente
ssh -i %USERPROFILE%\.ssh\id_ed25519_digitalocean root@IP_DEL_SERVIDOR "cd /opt/baserow && chmod +x deploy.sh && ./deploy.sh"
```

¡Ya tienes todo listo para conectarte de forma segura!
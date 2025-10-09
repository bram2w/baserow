# 🎯 Despliegue Completo de Baserow

## 🔑 SSH Configurado ✅
**Huella digital detectada:** `e5:d1:6a:4e:84:10:19:e9:56:c8:e4:bb:37:74:13:6e`

## 🚀 Opciones de Despliegue

### **Opción 1: Script PowerShell (Recomendado)**
```powershell
# Ejecutar en PowerShell (reemplaza IP_DEL_SERVIDOR)
.\Deploy-Baserow.ps1 -ServerIP IP_DEL_SERVIDOR
```

### **Opción 2: Comandos manuales**
```powershell
# 1. Subir archivos
scp -i "$env:USERPROFILE\.ssh\id_rsa" baserow-deploy.tar.gz root@IP_DEL_SERVIDOR:/opt/

# 2. Conectar y desplegar
ssh -i "$env:USERPROFILE\.ssh\id_rsa" root@IP_DEL_SERVIDOR
cd /opt && tar -xzf baserow-deploy.tar.gz
chmod +x deploy.sh && ./deploy.sh
```

### **Opción 3: Bash Script (si prefieres Bash)**
```bash
chmod +x deploy-remote.sh
./deploy-remote.sh IP_DEL_SERVIDOR
```

## 📋 Checklist Pre-Despliegue

### ✅ Preparación Local (Completado)
- [x] Claves SSH generadas
- [x] Archivos de configuración listos
- [x] Scripts de despliegue creados
- [x] Configuración para data.arrebolweddings.com

### 🎯 En DigitalOcean (Tu turno)
- [ ] Crear Droplet Ubuntu 22.04
- [ ] Agregar tu clave SSH pública
- [ ] Anotar la IP del servidor
- [ ] Configurar DNS: `data` → `IP_DEL_SERVIDOR`

## 🚀 Comando Final
Una vez que tengas el servidor listo:

```powershell
# En PowerShell, reemplaza 123.456.789.012 por la IP real
.\Deploy-Baserow.ps1 -ServerIP 123.456.789.012
```

## 📊 Resultado Esperado
- **URL:** https://data.arrebolweddings.com
- **SSL:** Automático con Let's Encrypt  
- **Tiempo total:** ~10-15 minutos
- **Estado final:** Baserow funcionando en producción

## 🔧 Post-Despliegue
```bash
# Ver logs
ssh -i "$env:USERPROFILE\.ssh\id_rsa" root@IP_DEL_SERVIDOR 'docker logs baserow_production'

# Reiniciar si es necesario
ssh -i "$env:USERPROFILE\.ssh\id_rsa" root@IP_DEL_SERVIDOR 'docker-compose -f /opt/docker-compose.production.yml restart'
```

¡Todo está listo para el despliegue! 🎉
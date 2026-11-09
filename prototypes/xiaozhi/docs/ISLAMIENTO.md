# Aislamiento del prototipo Xiaozhi

> Todo lo relacionado con Xiaozhi vive en DOS lugares y en ningún otro.
> Si se elimina el prototipo, FinaGotchi queda intacto.

## 1. Dónde vive cada cosa

| Ubicación | Contenido |
|---|---|
| `prototypes/xiaozhi/` (dentro del repo) | Puente, provisionamiento, MCP, pruebas y documentación |
| `C:\Users\ASUS\xiaozhi-server/` (fuera del repo) | Servidor Xiaozhi con Docker, `.config.yaml` con claves, modelo |
| `prototypes/xiaozhi/config.local.json` (ignorado por Git) | `device_token` secreto |

Ningún archivo del prototipo modifica:

- `backend/` (solo se consume el contrato existente)
- `simulator/` (propiedad del otro chat, no tocada)
- `frontend/` (fuera de alcance)
- `finagotchi.db` (se usa, nunca se versiona)
- Esquema, migraciones ni claves reales

## 2. Dependencias del prototipo

- El puente usa solo la **stdlib** de Python (`bridge.py`, `provisionar.py`, `cliente_prueba.py`).
- La única dependencia externa es `mcp[cli]`, declarada en `prototypes/xiaozhi/requirements.txt` y usada solo por `mcp_servidor.py`.
- No se agregan paquetes al `requirements.txt` principal ni al `backend/`.

## 3. Cómo eliminar el prototipo sin efectos

```powershell
# 1) Detener el puente (Ctrl+C en su terminal o cerrar el proceso bridge.py)

# 2) Detener el servidor Docker (si está corriendo)
cd C:\Users\ASUS\xiaozhi-server
docker compose down

# 3) Borrar el prototipo versionado
cd "G:\...\finagotchi"
git rm -r prototypes/xiaozhi
rmdir prototypes

# 4) Borrar lo que nunca se versionó
Remove-Item -Recurse -Force C:\Users\ASUS\xiaozhi-server   # fuera del repo

# 5) Verificar
git status
git log --oneline -1   # el último commit de FinaGotchi sigue igual
```

- `finagotchi.db`: los gastos de prueba (ids 508 y 509) quedan como datos locales; al borrar la carpeta no se pierde nada del código.
- El simulador, el backend y el frontend no dependen del prototipo de ninguna forma: nunca importan `prototypes/xiaozhi/`.
- El historial Git contiene el prototipo, pero eliminarlo del árbol no requiere reescribir historia: un `git rm` limpio basta.

## 4. Regla para futuras fases

1. Nada nuevo de Xiaozhi entra a `backend/`, `simulator/` o `frontend/` sin autorización explícita.
2. Un commit por fase del prototipo, siempre con ruta `prototypes/xiaozhi/`.
3. Sin `push` hasta autorización.
4. Cualquier clave/token nuevo va a `prototypes/xiaozhi/config.local.json` o a `C:\Users\ASUS\xiaozhi-server\data\.config.yaml`, nunca a Git.

# Publicar SIDE B en el repositorio vacío

Repositorio: `https://github.com/Leandro0210/Side_B` (rama predeterminada `master`).

El conector GitHub rechazó la escritura con **403 Resource not accessible by integration**. Por eso la importación inicial debe hacerse **desde tu PC** o reautorizar la integración con permisos efectivos de escritura (Contents y Pull requests).

## Inicializar con `SIDE_B_GitHub_Seguro.zip`

Descomprime ese paquete en una carpeta nueva, abre PowerShell y ejecuta:

```powershell
git init -b master
git add .
git status --short
git commit -m "feat: inicializar SIDE B con Gradio y controles éticos"
git remote add origin https://github.com/Leandro0210/Side_B.git
git push -u origin master
```

Antes de hacer commit, verifica que no figuren `.env`, `.venv`, respuestas `ratings/P*.csv`, `private/` ni `data/supervision/`. Si el repositorio deja de estar vacío no fuerces el push: integra primero el historial existente. GitHub puede solicitar autenticación mediante el administrador de credenciales; no pegues tokens en chats.

### Después de publicar

El código quedará versionado y las siguientes mejoras podrán realizarse con ramas y Pull Requests cuando la integración GitHub tenga permisos de escritura. El informe científico final se hará en formato paper, con la plantilla que proporcionará el docente.

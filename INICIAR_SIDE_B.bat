@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo [SIDE B] No existe el entorno virtual .venv
  echo Abre PowerShell aqui y ejecuta: py -m venv .venv
  echo Luego: .\.venv\Scripts\python.exe -m pip install -r requirements.txt
  pause
  exit /b 1
)
".venv\Scripts\python.exe" app_gradio.py
if errorlevel 1 (
  echo [SIDE B] La aplicacion no pudo iniciarse. Revisa el error de arriba.
  pause
)

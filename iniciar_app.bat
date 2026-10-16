@echo off
cd /d "%~dp0"

if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
) else (
    echo No se encontro el entorno virtual .venv
    echo Ejecuta: python -m venv .venv  y  pip install -r requirements.txt
    pause
    exit /b 1
)

streamlit run app/main.py
pause

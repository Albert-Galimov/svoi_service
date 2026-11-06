@echo off
chcp 65001 >nul
cd /d "%~dp0"

call .venv\Scripts\activate.bat
waitress-serve --listen=0.0.0.0:8000 --threads=8 config.wsgi:application
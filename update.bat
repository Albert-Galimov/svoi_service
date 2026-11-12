@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo === Останавливаем сервер (если открыт) ===
taskkill /FI "WINDOWTITLE eq Autoservice*" /T /F >nul 2>&1

echo === Получаем свежий код из git ===
git pull
if errorlevel 1 (
    echo [ОШИБКА] git pull не удался. Возможен конфликт.
    echo Проверьте "git status" и позвоните разработчику.
    pause
    exit /b 1
)

call venv\Scripts\activate.bat

echo === Устанавливаем новые зависимости (если появились) ===
pip install -r requirements.txt --quiet

echo === Применяем новые миграции (если есть) ===
python manage.py migrate --noinput

echo === Пересобираем статику (если менялась) ===
python manage.py collectstatic --noinput --clear

echo.
echo ==========================================
echo  Обновление завершено. Запускаю сервер.
echo ============================================
echo.

waitress-serve --listen=0.0.0.0:8000 --threads=8 config.wsgi:application

@echo off
chcp 65001 >nul
cd /d "%~dp0"

call venv\Scripts\activate.bat

REM --- 1. Копия базы с датой (на случай, если что-то пойдёт не так с ВК) ---
if not exist "backups" mkdir backups

for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set datetime=%%I
set YYYY=%datetime:~0,4%
set MM=%datetime:~4,2%
set DD=%datetime:~6,2%

set BACKUP_FILE=backups\db_%YYYY%-%MM%-%DD%.sqlite3

copy db.sqlite3 "%BACKUP_FILE%" >nul

REM --- 2. Отправка копии в ВК ---
REM Если отправка упадёт — копия останется локально, её можно будет переслать вручную.
python manage.py send_db_backup --file "%BACKUP_FILE%"

REM --- 3. Чистим старые копии (старше 30 дней) ---
forfiles /p backups /m db_*.sqlite3 /d -30 /c "cmd /c del @path" 2>nul
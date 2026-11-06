@echo off
chcp 65001 >nul
cd /d "%~dp0"

if not exist "backups" mkdir backups

for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set datetime=%%I
set YYYY=%datetime:~0,4%
set MM=%datetime:~4,2%
set DD=%datetime:~6,2%

copy db.sqlite3 "backups\db_%YYYY%-%MM%-%DD%.sqlite3"

forfiles /p backups /m db_*.sqlite3 /d -30 /c "cmd /c del @path" 2>nul

echo Бэкап создан: backups\db_%YYYY%-%MM%-%DD%.sqlite3
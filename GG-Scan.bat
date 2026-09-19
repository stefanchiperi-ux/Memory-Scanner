@echo off
setlocal
cd /d "%~dp0"
py -3 src\app.py
if errorlevel 1 (
  echo.
  echo Nu am putut porni cu comanda "py -3".
  echo Incearca manual: python src\app.py
  pause
)

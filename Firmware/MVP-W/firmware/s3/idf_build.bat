@echo off
REM Clear MSYS environment to allow ESP-IDF to run
set MSYSTEM=
set MSYS=
set MSYSTEM_CARCH=

REM Call ESP-IDF export
call C:\Espressif\frameworks\esp-idf-v5.2.1\export.bat
if errorlevel 1 (
    echo ESP-IDF export failed
    exit /b 1
)

REM Change to script directory
cd /d %~dp0

REM Run idf.py with all arguments passed to this script
idf.py %*

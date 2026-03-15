@echo off
REM MVP-W S3 Build Script
REM Run this script from Windows CMD (not from Git Bash/MSYS)

REM Clear MSYS environment variables
set MSYSTEM=
set MSYS=

REM Initialize ESP-IDF
call C:\Espressif\frameworks\esp-idf-v5.2.1\export.bat
if errorlevel 1 (
    echo Failed to initialize ESP-IDF
    exit /b 1
)

REM Navigate to project directory
cd /d %~dp0

REM Set target to ESP32-S3 (only needed once)
idf.py set-target esp32s3
if errorlevel 1 (
    echo Failed to set target
    exit /b 1
)

REM Build the project
idf.py build
if errorlevel 1 (
    echo Build failed
    exit /b 1
)

echo.
echo ========================================
echo Build successful!
echo ========================================
echo.
echo To flash, run:
echo   idf.py -p COMX flash monitor
echo.
echo Replace COMX with your COM port number.

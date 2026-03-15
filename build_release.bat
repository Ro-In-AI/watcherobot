@echo off
REM ============================================================
REM Build Release Binaries for WatcherRobot Body MCU
REM ============================================================

setlocal EnableDelayedExpansion

echo.
echo ========================================
echo  WatcherRobot Body - Build Release
echo ========================================
echo.

REM Check if IDF_PATH is set
if "%IDF_PATH%"=="" (
    echo [ERROR] IDF_PATH not set!
    echo Please run ESP-IDF export script first:
    echo   Windows: %%ESP_IDF_PATH%%\export.bat
    echo   Or install ESP-IDF and set IDF_PATH environment variable
    exit /b 1
)

REM Set project root
set "PROJECT_ROOT=%~dp0"
cd /d "%PROJECT_ROOT%"

REM Build the project
echo [1/2] Building project...
idf.py build
if errorlevel 1 (
    echo [ERROR] Build failed!
    exit /b 1
)

REM Copy binaries to release folder
echo [2/2] Copying binaries to release folder...
if not exist "%PROJECT_ROOT%release" mkdir "%PROJECT_ROOT%release"

copy /y "%PROJECT_ROOT%build\bootloader\bootloader.bin" "%PROJECT_ROOT%release\bootloader.bin" >nul
copy /y "%PROJECT_ROOT%build\partition_table\partition-table.bin" "%PROJECT_ROOT%release\partition-table.bin" >nul
copy /y "%PROJECT_ROOT%build\WatcherRobotBody.bin" "%PROJECT_ROOT%release\WatcherRobotBody.bin" >nul

echo.
echo ========================================
echo  Build Complete!
echo ========================================
echo.
echo Output files in release/:
echo   bootloader.bin       (0x0000)
echo   partition-table.bin  (0x8000)
echo   WatcherRobotBody.bin (0x10000)
echo.
echo Flash with: flash.bat COM_PORT
echo Example: flash.bat COM3
echo.

endlocal

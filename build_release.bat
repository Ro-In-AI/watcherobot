@echo off
REM ============================================================
REM Build Release Binary for WatcherRobot Body MCU
REM This creates a single flashable .bin file
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

REM Clean previous build
if exist "build\watcherobot_merged.bin" (
    echo [1/4] Cleaning previous release...
    del /q build\watcherobot_merged.bin 2>nul
)

REM Build the project
echo [2/4] Building project...
idf.py build
if errorlevel 1 (
    echo [ERROR] Build failed!
    exit /b 1
)

REM Create merged binary for easy flashing
echo [3/4] Creating merged binary...
esptool.py --chip esp32 merge_bin ^
    -o build/watcherobot_merged.bin ^
    --flash_mode dio ^
    --flash_size 4MB ^
    --flash_freq 40m ^
    0x0000 build/bootloader/bootloader.bin ^
    0x8000 build/partition_table/partition-table.bin ^
    0x10000 build/WatcherRobotBody.bin

if errorlevel 1 (
    echo [ERROR] Failed to create merged binary!
    exit /b 1
)

REM Copy to release folder
echo [4/4] Copying to release folder...
if not exist "%PROJECT_ROOT%release" mkdir "%PROJECT_ROOT%release"
copy /y "%PROJECT_ROOT%build\watcherobot_merged.bin" "%PROJECT_ROOT%release\watcherobot_merged.bin" >nul

echo.
echo ========================================
echo  Build Complete!
echo ========================================
echo.
echo Output files:
echo   build\watcherobot_merged.bin
echo   release\watcherobot_merged.bin  (for distribution)
echo.
echo Flash with: flash.bat COM_PORT
echo Example: flash.bat COM3
echo.

endlocal

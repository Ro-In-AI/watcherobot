@echo off
REM ============================================================
REM Flash Script for WatcherRobot Body MCU
REM Usage: flash.bat COM_PORT
REM Example: flash.bat COM3
REM ============================================================

setlocal EnableDelayedExpansion

set "PORT=%~1"
set "BAUD=921600"

echo.
echo ========================================
echo  WatcherRobot Body - Flash Tool
echo ========================================
echo.

REM Check if esptool is available
where esptool.py >nul 2>&1
if errorlevel 1 (
    echo [ERROR] esptool.py not found!
    echo Please run ESP-IDF export script first:
    echo   Windows: %%ESP_IDF_PATH%%\export.bat
    exit /b 1
)

REM Auto-detect COM port if not specified
if "%PORT%"=="" (
    echo [INFO] No COM port specified, auto-detecting...
    for /f "tokens=*" %%i in ('mode ^| findstr "COM[0-9]"') do (
        set "PORT=%%i"
        goto :found_port
    )
    echo [ERROR] No COM port found!
    echo Usage: flash.bat COM_PORT
    echo Example: flash.bat COM3
    exit /b 1
    :found_port
    echo [INFO] Found port: %PORT%
)

REM Set project root
set "PROJECT_ROOT=%~dp0"

REM Check if binaries exist (prefer release folder)
set "BIN_DIR="
if exist "%PROJECT_ROOT%release\bootloader.bin" (
    set "BIN_DIR=%PROJECT_ROOT%release"
) else if exist "%PROJECT_ROOT%build\bootloader\bootloader.bin" (
    set "BIN_DIR=%PROJECT_ROOT%build"
) else (
    echo [ERROR] Binary files not found!
    echo Please run build_release.bat first.
    exit /b 1
)

echo.
echo [INFO] Port: %PORT%
echo [INFO] Baud: %BAUD%
echo [INFO] Binary dir: %BIN_DIR%
echo.
echo [1/2] Entering bootloader mode...
echo       Please ensure the device is connected and in download mode.
echo.

REM Flash all binaries
echo [2/2] Flashing...
if "%BIN_DIR%"=="%PROJECT_ROOT%release" (
    esptool.py --chip esp32 -p "%PORT%" -b %BAUD% write_flash --flash_mode dio --flash_size 4MB --flash_freq 40m 0x0000 "%BIN_DIR%\bootloader.bin" 0x8000 "%BIN_DIR%\partition-table.bin" 0x10000 "%BIN_DIR%\WatcherRobotBody.bin"
) else (
    esptool.py --chip esp32 -p "%PORT%" -b %BAUD% write_flash --flash_mode dio --flash_size 4MB --flash_freq 40m 0x0000 "%BIN_DIR%\bootloader\bootloader.bin" 0x8000 "%BIN_DIR%\partition_table\partition-table.bin" 0x10000 "%BIN_DIR%\WatcherRobotBody.bin"
)

if errorlevel 1 (
    echo.
    echo [ERROR] Flash failed!
    echo Common issues:
    echo   - Wrong COM port
    echo   - Device not in bootloader mode (hold BOOT button while pressing RESET)
    echo   - Driver not installed (CH340/CP2102)
    exit /b 1
)

echo.
echo ========================================
echo  Flash Complete!
echo ========================================
echo.
echo Press any key to open serial monitor...
pause >nul

idf.py -p "%PORT%" monitor

endlocal

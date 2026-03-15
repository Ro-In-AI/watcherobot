@echo off
REM Watcher Server 启动脚本 (Windows)

echo ========================================
echo   Watcher Server 启动脚本
echo ========================================
echo.

REM 检查conda是否可用
where conda >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [错误] 未找到conda，请先安装Miniconda或Anaconda
    pause
    exit /b 1
)

REM 激活conda环境
echo [1/3] 激活conda环境: watcher-server...
call conda activate watcher-server
if %ERRORLEVEL% NEQ 0 (
    echo [错误] 环境 watcher-server 不存在
    echo 请先运行: conda env create -f environment.yml
    pause
    exit /b 1
)

REM 检查.env文件
echo [2/3] 检查配置文件...
if not exist .env (
    echo [警告] .env 文件不存在，从 .env.example 复制...
    copy .env.example .env
    echo [提示] 请编辑 .env 文件填入实际配置
    pause
)

REM 启动服务
echo [3/3] 启动服务...
echo.
python src/main.py

REM 服务结束后暂停
echo.
echo 服务已停止
pause

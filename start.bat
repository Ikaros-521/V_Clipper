@echo off
echo ========================================
echo SliceStream API - 视频切片微服务
echo ========================================
echo.

REM 检查 Python 是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Python，请先安装 Python 3.7+
    pause
    exit /b 1
)

REM 检查 FFmpeg 是否安装
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo [警告] 未检测到 FFmpeg，视频切片功能将无法使用
    echo [提示] 请安装 FFmpeg: https://ffmpeg.org/download.html
    echo.
)

REM 检查依赖是否安装
echo [检查] 正在检查依赖...
python -c "import fastapi" >nul 2>&1
if errorlevel 1 (
    echo [安装] 正在安装依赖包...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [错误] 依赖安装失败
        pause
        exit /b 1
    )
)

echo [启动] 正在启动服务...
echo.
python app.py

pause


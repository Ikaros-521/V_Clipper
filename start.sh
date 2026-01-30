#!/bin/bash

echo "========================================"
echo "SliceStream API - 视频切片微服务"
echo "========================================"
echo ""

# 检查 Python 是否安装
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未检测到 Python，请先安装 Python 3.7+"
    exit 1
fi

# 检查 FFmpeg 是否安装
if ! command -v ffmpeg &> /dev/null; then
    echo "[警告] 未检测到 FFmpeg，视频切片功能将无法使用"
    echo "[提示] 请安装 FFmpeg:"
    echo "  - Ubuntu/Debian: sudo apt install ffmpeg"
    echo "  - macOS: brew install ffmpeg"
    echo ""
fi

# 检查依赖是否安装
echo "[检查] 正在检查依赖..."
if ! python3 -c "import fastapi" &> /dev/null; then
    echo "[安装] 正在安装依赖包..."
    pip3 install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "[错误] 依赖安装失败"
        exit 1
    fi
fi

echo "[启动] 正在启动服务..."
echo ""
python3 app.py


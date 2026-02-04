"""
视频切片服务配置文件
"""
from pathlib import Path

# 服务配置
HOST = "0.0.0.0"
PORT = 8700

# 目录配置
BASE_DIR = Path("media_data")
UPLOAD_DIR = BASE_DIR / "uploads"
SEGMENT_DIR = BASE_DIR / "segments"

# 清理配置
CLEANUP_INTERVAL_HOURS = 1  # 每隔多少小时执行一次清理
FILE_EXPIRY_HOURS = 2       # 清理多少小时前的文件

# FFmpeg 默认参数
DEFAULT_SCALE = "1080:-2"    # 默认分辨率（-2 确保输出为偶数，H.264 要求）
DEFAULT_FPS = 25            # 默认帧率
DEFAULT_CRF = 23            # 默认质量（越小质量越高，范围0-51）
DEFAULT_PRESET = "ultrafast"  # 默认编码速度预设

# 日志配置
LOG_LEVEL = "INFO"


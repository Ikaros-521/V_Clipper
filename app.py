import os
import uuid
import subprocess
import hashlib
import time
import asyncio
from datetime import datetime, timedelta
from fastapi import FastAPI, UploadFile, File, HTTPException, Query, BackgroundTasks, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from typing import Optional, Literal
import logging

# 导入配置
try:
    from config import (
        HOST, PORT, BASE_DIR, UPLOAD_DIR, SEGMENT_DIR,
        CLEANUP_INTERVAL_HOURS, FILE_EXPIRY_HOURS,
        DEFAULT_SCALE, DEFAULT_FPS, DEFAULT_CRF, DEFAULT_PRESET,
        LOG_LEVEL
    )
except ImportError:
    # 如果没有配置文件，使用默认配置
    HOST = "0.0.0.0"
    PORT = 8700
    BASE_DIR = Path("media_data")
    UPLOAD_DIR = BASE_DIR / "uploads"
    SEGMENT_DIR = BASE_DIR / "segments"
    CLEANUP_INTERVAL_HOURS = 1
    FILE_EXPIRY_HOURS = 2
    DEFAULT_SCALE = "480:-1"
    DEFAULT_FPS = 10
    DEFAULT_CRF = 28
    DEFAULT_PRESET = "ultrafast"
    LOG_LEVEL = "INFO"

# 配置日志
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="V_Clipper API", 
    description="专用视频切片微服务 - 支持自动清理和灵活返回方式",
    version="1.0.0"
)

# 创建目录
for d in [UPLOAD_DIR, SEGMENT_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# 挂载静态文件目录（用于URL访问）
app.mount("/media", StaticFiles(directory=str(SEGMENT_DIR)), name="media")

def generate_file_id(file_content: bytes):
    return hashlib.sha256(file_content).hexdigest()[:16]

@app.post("/upload", summary="上传原始视频")
async def upload_video(file: UploadFile = File(...)):
    content = await file.read()
    file_id = generate_file_id(content)
    
    # 检查是否已存在
    file_path = UPLOAD_DIR / f"{file_id}{Path(file.filename).suffix}"
    if not file_path.exists():
        with open(file_path, "wb") as f:
            f.write(content)
    
    return {"file_id": file_id, "filename": file.filename}

@app.get("/clip", summary="执行切片并返回文件或URL")
async def clip_video(
    request: Request,
    file_id: str,
    start: float = Query(..., description="起始时间（秒）"),
    duration: Optional[float] = Query(None, description="持续时间（秒），与end二选一"),
    end: Optional[float] = Query(None, description="结束时间（秒），与duration二选一"),
    # 返回类型控制
    return_type: Literal["file", "url"] = Query("file", description="返回类型：file(直接返回文件) 或 url(返回访问链接)"),
    # 进阶参数配置
    scale: Optional[str] = Query(DEFAULT_SCALE, description="分辨率缩放，如 480:-1"),
    fps: Optional[int] = Query(DEFAULT_FPS, description="目标帧率"),
    crf: Optional[int] = Query(DEFAULT_CRF, description="质量控制 (0-51，越小质量越高)"),
    preset: Optional[str] = Query(DEFAULT_PRESET, description="编码速度预设")
):
    # 0. 参数验证：duration 和 end 必须提供其中一个
    if duration is None and end is None:
        raise HTTPException(
            status_code=400, 
            detail="必须提供 duration（持续时间）或 end（结束时间）参数之一"
        )
    
    if duration is not None and end is not None:
        raise HTTPException(
            status_code=400, 
            detail="duration 和 end 参数不能同时提供，请只使用其中一个"
        )
    
    # 计算实际的持续时间
    if end is not None:
        if end <= start:
            raise HTTPException(
                status_code=400, 
                detail=f"结束时间（{end}）必须大于起始时间（{start}）"
            )
        actual_duration = end - start
        time_mode = "range"  # 起止时间模式
    else:
        if duration <= 0:
            raise HTTPException(
                status_code=400, 
                detail=f"持续时间（{duration}）必须大于0"
            )
        actual_duration = duration
        time_mode = "duration"  # 持续时间模式
    
    # 1. 查找源文件 (支持 mp4, mov, mkv 等)
    source_files = list(UPLOAD_DIR.glob(f"{file_id}.*"))
    if not source_files:
        raise HTTPException(status_code=404, detail="未找到对应的原始视频，请先上传")
    
    video_path = source_files[0]
    # 使用更安全的文件名（替换特殊字符）
    safe_scale = scale.replace(":", "_")
    # 文件名包含实际的持续时间
    output_filename = f"{file_id}_{start}_{actual_duration}_{safe_scale}_{fps}.mp4"
    output_path = SEGMENT_DIR / output_filename

    # 2. 如果切片不存在，执行切片
    if not output_path.exists():
        # 3. 构建极速切片命令
        # 针对 VLM 优化：降分辨率、降帧、无音频、极速预设
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(start),
            "-t", str(actual_duration),
            "-i", str(video_path),
            "-vf", f"scale={scale},fps={fps}",
            "-c:v", "libx264",
            "-preset", preset,
            "-crf", str(crf),
            "-an",  # 默认禁掉音频，VLM 不需要
            str(output_path)
        ]

        try:
            # 运行 FFmpeg
            logger.info(f"开始切片: {output_filename} (模式: {time_mode}, start={start}, duration={actual_duration})")
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            logger.info(f"切片完成: {output_filename}")
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr if e.stderr else str(e)
            logger.error(f"FFmpeg 切片失败: {error_msg}")
            raise HTTPException(status_code=500, detail=f"FFmpeg 切片失败: {error_msg}")
        except FileNotFoundError:
            raise HTTPException(status_code=500, detail="FFmpeg 未安装或未在系统PATH中")

    # 4. 根据返回类型返回结果
    response_data = {
        "filename": output_filename,
        "file_id": file_id,
        "start": start,
        "duration": actual_duration,
        "size_bytes": output_path.stat().st_size
    }
    
    # 添加结束时间信息（如果使用的是起止时间模式）
    if end is not None:
        response_data["end"] = end
    
    if return_type == "url":
        # 构建完整的URL
        base_url = str(request.base_url).rstrip('/')
        file_url = f"{base_url}/media/{output_filename}"
        response_data["url"] = file_url
        return JSONResponse(response_data)
    else:
        # 直接返回文件
        return FileResponse(
            output_path,
            media_type="video/mp4",
            filename=output_filename
        )

def cleanup_old_files(hours: int = FILE_EXPIRY_HOURS):
    """清理指定小时前的文件"""
    now = datetime.now()
    expiry_time = now - timedelta(hours=hours)
    
    deleted_count = 0
    total_size = 0
    
    # 清理切片文件
    for file_path in SEGMENT_DIR.glob("*"):
        if file_path.is_file():
            file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
            if file_mtime < expiry_time:
                file_size = file_path.stat().st_size
                try:
                    file_path.unlink()
                    deleted_count += 1
                    total_size += file_size
                    logger.info(f"已删除过期切片: {file_path.name}")
                except Exception as e:
                    logger.error(f"删除文件失败 {file_path.name}: {e}")
    
    # 清理上传文件（可选，根据需求决定是否清理原始视频）
    for file_path in UPLOAD_DIR.glob("*"):
        if file_path.is_file():
            file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
            if file_mtime < expiry_time:
                file_size = file_path.stat().st_size
                try:
                    file_path.unlink()
                    deleted_count += 1
                    total_size += file_size
                    logger.info(f"已删除过期上传: {file_path.name}")
                except Exception as e:
                    logger.error(f"删除文件失败 {file_path.name}: {e}")
    
    logger.info(f"清理完成: 删除 {deleted_count} 个文件, 释放 {total_size / 1024 / 1024:.2f} MB")
    return deleted_count, total_size

async def periodic_cleanup():
    """定期清理任务"""
    while True:
        try:
            logger.info("开始定期清理任务...")
            cleanup_old_files(FILE_EXPIRY_HOURS)
        except Exception as e:
            logger.error(f"定期清理任务出错: {e}")
        
        # 等待下一次清理
        await asyncio.sleep(CLEANUP_INTERVAL_HOURS * 3600)

@app.on_event("startup")
async def startup_event():
    """应用启动时启动定期清理任务"""
    logger.info(f"启动定期清理任务: 每 {CLEANUP_INTERVAL_HOURS} 小时清理 {FILE_EXPIRY_HOURS} 小时前的文件")
    asyncio.create_task(periodic_cleanup())

@app.delete("/cleanup", summary="手动清理过期文件")
async def manual_cleanup(hours: int = Query(FILE_EXPIRY_HOURS, description="清理多少小时前的文件")):
    """手动触发清理任务"""
    try:
        deleted_count, total_size = cleanup_old_files(hours)
        return {
            "success": True,
            "deleted_count": deleted_count,
            "freed_space_mb": round(total_size / 1024 / 1024, 2),
            "hours": hours
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清理失败: {str(e)}")

@app.get("/stats", summary="获取存储统计信息")
async def get_stats():
    """获取当前存储使用情况"""
    def get_dir_size(directory: Path):
        total_size = 0
        file_count = 0
        for file_path in directory.glob("*"):
            if file_path.is_file():
                total_size += file_path.stat().st_size
                file_count += 1
        return file_count, total_size
    
    upload_count, upload_size = get_dir_size(UPLOAD_DIR)
    segment_count, segment_size = get_dir_size(SEGMENT_DIR)
    
    return {
        "uploads": {
            "count": upload_count,
            "size_mb": round(upload_size / 1024 / 1024, 2)
        },
        "segments": {
            "count": segment_count,
            "size_mb": round(segment_size / 1024 / 1024, 2)
        },
        "total_size_mb": round((upload_size + segment_size) / 1024 / 1024, 2),
        "cleanup_config": {
            "interval_hours": CLEANUP_INTERVAL_HOURS,
            "expiry_hours": FILE_EXPIRY_HOURS
        }
    }

if __name__ == "__main__":
    import uvicorn
    logger.info(f"启动 SliceStream API 服务: {HOST}:{PORT}")
    logger.info(f"清理配置: 每 {CLEANUP_INTERVAL_HOURS} 小时清理 {FILE_EXPIRY_HOURS} 小时前的文件")
    uvicorn.run(app, host=HOST, port=PORT)
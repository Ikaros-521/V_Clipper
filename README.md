# V_Clipper API - 视频切片微服务

专用于视频切片的高性能微服务，支持自动清理和灵活的返回方式。

## 功能特性

✅ **视频上传与切片** - 支持多种视频格式（mp4, mov, mkv等）  
✅ **灵活返回方式** - 支持直接返回文件或返回URL链接  
✅ **自动定时清理** - 定时自动清理过期文件，节省存储空间  
✅ **手动清理接口** - 支持手动触发清理任务  
✅ **存储统计** - 实时查看存储使用情况  
✅ **高性能切片** - 针对VLM优化的FFmpeg参数配置  

## 快速开始

### 安装依赖

```bash
pip install fastapi uvicorn python-multipart
```

确保系统已安装 FFmpeg：
```bash
# Windows (使用 Chocolatey)
choco install ffmpeg

# Linux
sudo apt install ffmpeg

# macOS
brew install ffmpeg
```

### 启动服务

```bash
python app.py
```

服务将在 `http://localhost:8700` 启动

## API 接口文档

### 1. 上传视频

**POST** `/upload`

上传原始视频文件，返回唯一的 file_id。

**请求示例：**
```bash
curl -X POST "http://localhost:8700/upload" \
  -F "file=@video.mp4"
```

**响应示例：**
```json
{
  "file_id": "a1b2c3d4e5f6g7h8",
  "filename": "video.mp4"
}
```

---

### 2. 切片视频

**GET** `/clip`

根据时间范围切片视频，支持返回文件或URL。

**时间参数支持两种方式：**
1. **起始时间 + 持续时间**：`start` + `duration`
2. **起始时间 + 结束时间**：`start` + `end`

**参数说明：**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| file_id | string | ✅ | - | 上传视频返回的ID |
| start | float | ✅ | - | 起始时间（秒） |
| duration | float | ⚠️ | - | 持续时间（秒），与end二选一 |
| end | float | ⚠️ | - | 结束时间（秒），与duration二选一 |
| return_type | string | ❌ | file | 返回类型：`file` 或 `url` |
| scale | string | ❌ | 480:-1 | 分辨率缩放 |
| fps | int | ❌ | 10 | 帧率 |
| crf | int | ❌ | 28 | 质量控制（0-51） |
| preset | string | ❌ | ultrafast | 编码速度预设 |

**请求示例1（使用持续时间）：**
```bash
# 从第10秒开始，持续5秒
curl "http://localhost:8700/clip?file_id=a1b2c3d4e5f6g7h8&start=10&duration=5" \
  --output clip.mp4
```

**请求示例2（使用起止时间）：**
```bash
# 从第10秒到第15秒
curl "http://localhost:8700/clip?file_id=a1b2c3d4e5f6g7h8&start=10&end=15" \
  --output clip.mp4
```

**请求示例3（返回URL）：**
```bash
curl "http://localhost:8700/clip?file_id=a1b2c3d4e5f6g7h8&start=10&duration=5&return_type=url"
```

**响应示例（URL模式，使用duration）：**
```json
{
  "url": "http://localhost:8700/media/a1b2c3d4e5f6g7h8_10_5_480_-1_10.mp4",
  "filename": "a1b2c3d4e5f6g7h8_10_5_480_-1_10.mp4",
  "file_id": "a1b2c3d4e5f6g7h8",
  "start": 10,
  "duration": 5,
  "size_bytes": 524288
}
```

**响应示例（URL模式，使用end）：**
```json
{
  "url": "http://localhost:8700/media/a1b2c3d4e5f6g7h8_10_5_480_-1_10.mp4",
  "filename": "a1b2c3d4e5f6g7h8_10_5_480_-1_10.mp4",
  "file_id": "a1b2c3d4e5f6g7h8",
  "start": 10,
  "duration": 5,
  "end": 15,
  "size_bytes": 524288
}
```

---

### 3. 手动清理过期文件

**DELETE** `/cleanup`

手动触发清理任务，删除指定小时前的文件。

**参数说明：**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| hours | int | ❌ | 2 | 清理多少小时前的文件 |

**请求示例：**
```bash
curl -X DELETE "http://localhost:8700/cleanup?hours=3"
```

**响应示例：**
```json
{
  "success": true,
  "deleted_count": 15,
  "freed_space_mb": 234.56,
  "hours": 3
}
```

---

### 4. 获取存储统计

**GET** `/stats`

查看当前存储使用情况和清理配置。

**请求示例：**
```bash
curl "http://localhost:8700/stats"
```

**响应示例：**
```json
{
  "uploads": {
    "count": 5,
    "size_mb": 150.25
  },
  "segments": {
    "count": 23,
    "size_mb": 89.67
  },
  "total_size_mb": 239.92,
  "cleanup_config": {
    "interval_hours": 1,
    "expiry_hours": 2
  }
}
```

---

## 配置说明

在 `config.py` 中可以修改以下配置：

```python
# 清理配置
CLEANUP_INTERVAL_HOURS = 1  # 每隔多少小时执行一次清理
FILE_EXPIRY_HOURS = 2       # 清理多少小时前的文件

# FFmpeg 默认参数
DEFAULT_SCALE = "480:-1"    # 默认分辨率
DEFAULT_FPS = 10            # 默认帧率
DEFAULT_CRF = 28            # 默认质量（越小质量越高）
DEFAULT_PRESET = "ultrafast"  # 默认编码速度
```

## 自动清理机制

服务启动后会自动启动定期清理任务：

- **清理间隔**：每 1 小时执行一次（可配置）
- **清理规则**：删除 2 小时前的文件（可配置）
- **清理范围**：包括上传的原始视频和生成的切片文件
- **日志记录**：所有清理操作都会记录到日志

## 使用场景

### 场景1：VLM视频分析
```python
import requests

# 1. 上传视频
with open("video.mp4", "rb") as f:
    resp = requests.post("http://localhost:8700/upload", files={"file": f})
    file_id = resp.json()["file_id"]

# 2. 获取切片URL（用于VLM分析）
resp = requests.get(f"http://localhost:8700/clip", params={
    "file_id": file_id,
    "start": 10,
    "duration": 5,
    "return_type": "url",
    "scale": "480:-1",
    "fps": 10
})
video_url = resp.json()["url"]

# 3. 将URL传给VLM进行分析
# analyze_video(video_url)
```

### 场景2：批量下载切片
```python
import requests

file_id = "a1b2c3d4e5f6g7h8"
segments = [(0, 5), (5, 5), (10, 5)]  # 起始时间和持续时间

for i, (start, duration) in enumerate(segments):
    resp = requests.get(f"http://localhost:8700/clip", params={
        "file_id": file_id,
        "start": start,
        "duration": duration,
        "return_type": "file"
    })
    
    with open(f"segment_{i}.mp4", "wb") as f:
        f.write(resp.content)
```

## 目录结构

```
V_Clipper/
├── app.py              # 主应用文件
├── config.py           # 配置文件
├── README.md           # 文档
└── media_data/         # 数据目录（自动创建）
    ├── uploads/        # 上传的原始视频
    └── segments/       # 生成的切片文件
```

## 注意事项

1. **存储空间**：确保有足够的磁盘空间存储视频文件
2. **FFmpeg依赖**：必须安装FFmpeg才能正常工作
3. **文件清理**：自动清理会删除原始上传文件，如需保留请修改 `cleanup_old_files` 函数
4. **并发处理**：大量并发切片请求可能占用较多CPU资源
5. **URL访问**：返回的URL仅在文件未被清理前有效

## API文档

启动服务后访问：
- Swagger UI: `http://localhost:8700/docs`
- ReDoc: `http://localhost:8700/redoc`

## License

MIT


# 视频信息获取功能说明

## 📹 功能概述

视频切片服务现在支持自动获取和查询视频的详细信息，包括时长、分辨率、帧率、编码格式、比特率等元数据。

## 🎯 核心功能

### 1. 上传时自动获取
上传视频后，服务会自动使用 `ffprobe` 分析视频，并在响应中返回完整的视频信息。

### 2. 独立查询接口
可以随时通过 `file_id` 查询已上传视频的详细信息。

### 3. 智能批量切片
根据视频时长自动计算切片数量，无需手动指定。

---

## 📊 视频信息字段说明

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `duration` | float | 视频时长（秒） | 120.5 |
| `width` | int | 视频宽度（像素） | 1920 |
| `height` | int | 视频高度（像素） | 1080 |
| `fps` | float | 帧率（帧/秒） | 30.0 |
| `codec` | string | 视频编码格式 | "h264" |
| `bitrate_kbps` | float | 比特率（kbps） | 5000.0 |
| `size_mb` | float | 文件大小（MB） | 75.5 |

---

## 🔧 使用方式

### 方式1: 上传时获取

**请求：**
```bash
curl -X POST "http://localhost:8700/upload" \
  -F "file=@video.mp4"
```

**响应：**
```json
{
  "file_id": "a1b2c3d4e5f6g7h8",
  "filename": "video.mp4",
  "is_new": true,
  "video_info": {
    "duration": 120.5,
    "width": 1920,
    "height": 1080,
    "fps": 30.0,
    "codec": "h264",
    "bitrate_kbps": 5000.0,
    "size_mb": 75.5
  }
}
```

**Python 示例：**
```python
import requests

with open("video.mp4", "rb") as f:
    response = requests.post("http://localhost:8700/upload", files={"file": f})
    data = response.json()
    
    print(f"File ID: {data['file_id']}")
    print(f"时长: {data['video_info']['duration']}秒")
    print(f"分辨率: {data['video_info']['width']}x{data['video_info']['height']}")
    print(f"帧率: {data['video_info']['fps']} fps")
```

---

### 方式2: 独立查询

**请求：**
```bash
curl "http://localhost:8700/video/a1b2c3d4e5f6g7h8"
```

**响应：**
```json
{
  "file_id": "a1b2c3d4e5f6g7h8",
  "filename": "a1b2c3d4e5f6g7h8.mp4",
  "video_info": {
    "duration": 120.5,
    "width": 1920,
    "height": 1080,
    "fps": 30.0,
    "codec": "h264",
    "bitrate_kbps": 5000.0,
    "size_mb": 75.5
  }
}
```

**Python 示例：**
```python
import requests

response = requests.get("http://localhost:8700/video/a1b2c3d4e5f6g7h8")
data = response.json()

print(f"视频信息:")
print(f"  时长: {data['video_info']['duration']}秒")
print(f"  分辨率: {data['video_info']['width']}x{data['video_info']['height']}")
print(f"  帧率: {data['video_info']['fps']} fps")
print(f"  编码: {data['video_info']['codec']}")
print(f"  比特率: {data['video_info']['bitrate_kbps']} kbps")
print(f"  大小: {data['video_info']['size_mb']} MB")
```

---

## 💡 实际应用场景

### 场景1: 智能批量切片

根据视频时长自动计算切片数量：

```python
import requests

# 上传视频
with open("video.mp4", "rb") as f:
    response = requests.post("http://localhost:8700/upload", files={"file": f})
    data = response.json()
    
    file_id = data['file_id']
    duration = data['video_info']['duration']
    
    print(f"视频总时长: {duration}秒")

# 自动切片（每10秒一段）
clip_length = 10
clip_count = int(duration / clip_length) + 1

print(f"将切分为 {clip_count} 个片段")

for i in range(clip_count):
    start = i * clip_length
    end = min((i + 1) * clip_length, duration)
    
    response = requests.get("http://localhost:8700/clip", params={
        "file_id": file_id,
        "start": start,
        "end": end,
        "return_type": "url"
    })
    
    clip_url = response.json()["url"]
    print(f"片段 {i+1}: {start}s - {end}s -> {clip_url}")
```

---

### 场景2: 根据分辨率选择切片参数

根据原始视频分辨率智能选择切片参数：

```python
import requests

# 上传并获取视频信息
with open("video.mp4", "rb") as f:
    response = requests.post("http://localhost:8700/upload", files={"file": f})
    data = response.json()
    
    file_id = data['file_id']
    width = data['video_info']['width']
    height = data['video_info']['height']
    fps = data['video_info']['fps']

# 根据原始分辨率选择目标分辨率
if width >= 1920:
    target_scale = "720:-1"  # 720p
    target_fps = 15
elif width >= 1280:
    target_scale = "480:-1"  # 480p
    target_fps = 10
else:
    target_scale = "320:-1"  # 320p
    target_fps = 5

print(f"原始分辨率: {width}x{height} @ {fps}fps")
print(f"目标参数: {target_scale} @ {target_fps}fps")

# 使用优化的参数切片
response = requests.get("http://localhost:8700/clip", params={
    "file_id": file_id,
    "start": 0,
    "duration": 10,
    "scale": target_scale,
    "fps": target_fps,
    "return_type": "url"
})

print(f"切片URL: {response.json()['url']}")
```

---

### 场景3: 视频质量检查

在切片前检查视频质量：

```python
import requests

def check_video_quality(file_id):
    """检查视频质量是否符合要求"""
    response = requests.get(f"http://localhost:8700/video/{file_id}")
    info = response.json()['video_info']
    
    issues = []
    
    # 检查分辨率
    if info['width'] < 640 or info['height'] < 480:
        issues.append(f"分辨率过低: {info['width']}x{info['height']}")
    
    # 检查帧率
    if info['fps'] < 15:
        issues.append(f"帧率过低: {info['fps']} fps")
    
    # 检查比特率
    if info['bitrate_kbps'] < 500:
        issues.append(f"比特率过低: {info['bitrate_kbps']} kbps")
    
    # 检查时长
    if info['duration'] < 1:
        issues.append(f"视频过短: {info['duration']}秒")
    
    if issues:
        print("⚠️  视频质量问题:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    else:
        print("✅ 视频质量检查通过")
        return True

# 使用示例
file_id = "your_file_id"
if check_video_quality(file_id):
    # 继续处理
    pass
```

---

### 场景4: 生成视频摘要

```python
import requests

def generate_video_summary(file_id):
    """生成视频摘要信息"""
    response = requests.get(f"http://localhost:8700/video/{file_id}")
    data = response.json()
    info = data['video_info']
    
    # 计算视频时长（格式化）
    duration = info['duration']
    minutes = int(duration // 60)
    seconds = int(duration % 60)
    
    # 计算分辨率类型
    if info['width'] >= 3840:
        resolution_type = "4K"
    elif info['width'] >= 1920:
        resolution_type = "Full HD"
    elif info['width'] >= 1280:
        resolution_type = "HD"
    else:
        resolution_type = "SD"
    
    # 计算帧率类型
    if info['fps'] >= 60:
        fps_type = "高帧率"
    elif info['fps'] >= 30:
        fps_type = "标准帧率"
    else:
        fps_type = "低帧率"
    
    summary = f"""
视频摘要
========================================
文件ID: {file_id}
文件名: {data['filename']}
时长: {minutes}分{seconds}秒
分辨率: {info['width']}x{info['height']} ({resolution_type})
帧率: {info['fps']} fps ({fps_type})
编码: {info['codec'].upper()}
比特率: {info['bitrate_kbps']} kbps
文件大小: {info['size_mb']} MB
========================================
    """
    
    return summary

# 使用示例
print(generate_video_summary("your_file_id"))
```

---

## ⚙️ 技术实现

### 使用 ffprobe 获取信息

服务使用 `ffprobe` 命令行工具获取视频元数据：

```bash
ffprobe -v quiet -print_format json -show_format -show_streams video.mp4
```

### 依赖要求

- ✅ **FFmpeg**: 必须安装 FFmpeg 套件（包含 ffprobe）
- ✅ **系统PATH**: ffprobe 必须在系统 PATH 中可访问

### 安装 FFmpeg

**Windows:**
```bash
choco install ffmpeg
```

**Linux:**
```bash
sudo apt install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

---

## ⚠️ 注意事项

### 1. ffprobe 未安装
如果 ffprobe 未安装，上传接口仍然可以工作，但 `video_info` 字段将为 `null`：

```json
{
  "file_id": "abc123",
  "filename": "video.mp4",
  "is_new": true,
  "video_info": null
}
```

### 2. 视频格式支持
支持所有 FFmpeg 支持的视频格式，包括：
- MP4 (.mp4)
- MOV (.mov)
- AVI (.avi)
- MKV (.mkv)
- WebM (.webm)
- FLV (.flv)
- 等等...

### 3. 性能考虑
- 获取视频信息通常很快（< 1秒）
- 对于超大文件（> 1GB），可能需要几秒钟
- 信息获取不会影响文件上传速度

---

## 🎉 总结

视频信息获取功能让你能够：

1. ✅ **自动获取**: 上传时自动返回视频详细信息
2. ✅ **随时查询**: 通过 file_id 随时查询视频信息
3. ✅ **智能处理**: 根据视频属性智能选择处理参数
4. ✅ **质量检查**: 在处理前验证视频质量
5. ✅ **批量优化**: 根据时长自动计算切片策略

这使得视频处理流程更加智能和自动化！


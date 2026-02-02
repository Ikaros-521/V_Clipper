# 使用示例

## 快速开始

### 1. 启动服务

**Windows:**
```bash
start.bat
```

**Linux/Mac:**
```bash
chmod +x start.sh
./start.sh
```

**或者直接运行:**
```bash
python app.py
```

服务启动后访问: http://localhost:8700/docs

---

## Python 客户端示例

### 示例 1: 基本使用流程（使用持续时间）

```python
import requests

BASE_URL = "http://localhost:8700"

# 1. 上传视频
with open("my_video.mp4", "rb") as f:
    response = requests.post(f"{BASE_URL}/upload", files={"file": f})
    data = response.json()
    file_id = data["file_id"]
    video_info = data["video_info"]
    
    print(f"上传成功，File ID: {file_id}")
    print(f"视频时长: {video_info['duration']}秒")
    print(f"分辨率: {video_info['width']}x{video_info['height']}")
    print(f"帧率: {video_info['fps']} fps")
    print(f"文件大小: {video_info['size_mb']} MB")

# 2. 切片视频（使用 start + duration）
response = requests.get(f"{BASE_URL}/clip", params={
    "file_id": file_id,
    "start": 10,      # 从第10秒开始
    "duration": 5,    # 持续5秒
    "return_type": "file"
})

with open("output_clip.mp4", "wb") as f:
    f.write(response.content)
    print("切片已保存到 output_clip.mp4")
```

### 示例 1.2: 基本使用流程（使用起止时间）

```python
import requests

BASE_URL = "http://localhost:8700"

# 1. 上传视频
with open("my_video.mp4", "rb") as f:
    response = requests.post(f"{BASE_URL}/upload", files={"file": f})
    file_id = response.json()["file_id"]
    print(f"上传成功，File ID: {file_id}")

# 2. 切片视频（使用 start + end）
response = requests.get(f"{BASE_URL}/clip", params={
    "file_id": file_id,
    "start": 10,      # 从第10秒开始
    "end": 15,        # 到第15秒结束
    "return_type": "file"
})

with open("output_clip.mp4", "wb") as f:
    f.write(response.content)
    print("切片已保存到 output_clip.mp4")
```

### 示例 2: 获取URL用于VLM分析

```python
import requests

BASE_URL = "http://localhost:8700"

def get_video_clip_url(file_id: str, start: float, duration: float = None, end: float = None):
    """
    获取视频切片的URL
    支持两种方式：
    1. start + duration（起始时间 + 持续时间）
    2. start + end（起始时间 + 结束时间）
    """
    params = {
        "file_id": file_id,
        "start": start,
        "return_type": "url",
        "scale": "480:-1",  # 480p分辨率
        "fps": 10           # 10帧/秒
    }
    
    # 添加时间参数（二选一）
    if duration is not None:
        params["duration"] = duration
    elif end is not None:
        params["end"] = end
    else:
        raise ValueError("必须提供 duration 或 end 参数之一")
    
    response = requests.get(f"{BASE_URL}/clip", params=params)
    
    if response.status_code == 200:
        return response.json()["url"]
    else:
        raise Exception(f"切片失败: {response.text}")

# 使用示例1：使用持续时间
file_id = "your_file_id_here"
video_url = get_video_clip_url(file_id, start=0, duration=10)
print(f"视频URL（0-10秒）: {video_url}")

# 使用示例2：使用起止时间
video_url = get_video_clip_url(file_id, start=5, end=15)
print(f"视频URL（5-15秒）: {video_url}")

# 将URL传给VLM进行分析
# vlm_result = analyze_video_with_vlm(video_url)
```

### 示例 2.2: 查询视频信息

```python
import requests

BASE_URL = "http://localhost:8700"

def get_video_info(file_id: str):
    """获取已上传视频的详细信息"""
    response = requests.get(f"{BASE_URL}/video/{file_id}")
    
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"获取视频信息失败: {response.text}")

# 使用示例
file_id = "your_file_id_here"
info = get_video_info(file_id)

print(f"文件名: {info['filename']}")
print(f"时长: {info['video_info']['duration']}秒")
print(f"分辨率: {info['video_info']['width']}x{info['video_info']['height']}")
print(f"帧率: {info['video_info']['fps']} fps")
print(f"编码: {info['video_info']['codec']}")
print(f"比特率: {info['video_info']['bitrate_kbps']} kbps")
print(f"大小: {info['video_info']['size_mb']} MB")

# 根据视频时长动态切片
duration = info['video_info']['duration']
clip_length = 10  # 每段10秒

for start in range(0, int(duration), clip_length):
    clip_url = get_video_clip_url(file_id, start=start, duration=clip_length)
    print(f"切片 {start}-{start+clip_length}秒: {clip_url}")
```

### 示例 3: 批量切片

```python
import requests
from concurrent.futures import ThreadPoolExecutor

BASE_URL = "http://localhost:8700"

def create_clip(file_id: str, start: float, duration: float = None, end: float = None, index: int = 0):
    """创建单个切片"""
    params = {
        "file_id": file_id,
        "start": start,
        "return_type": "url"
    }
    
    if duration is not None:
        params["duration"] = duration
    elif end is not None:
        params["end"] = end
    
    response = requests.get(f"{BASE_URL}/clip", params=params)
    
    if response.status_code == 200:
        data = response.json()
        print(f"切片 {index}: {data['url']}")
        return data
    else:
        print(f"切片 {index} 失败: {response.text}")
        return None

# 先上传视频并获取视频信息
with open("video.mp4", "rb") as f:
    response = requests.post(f"{BASE_URL}/upload", files={"file": f})
    data = response.json()
    file_id = data["file_id"]
    video_duration = data["video_info"]["duration"]
    
    print(f"视频总时长: {video_duration}秒")

# 方式1：使用持续时间批量创建切片（每5秒一个片段）
clip_duration = 5    # 每个切片5秒

segments = []
for i in range(0, int(video_duration), clip_duration):
    segments.append((file_id, i, clip_duration, None, i // clip_duration))

# 方式2：使用起止时间批量创建切片
# segments = []
# time_ranges = [(0, 10), (10, 20), (20, 30), (30, 40)]  # 起止时间对
# for idx, (start, end) in enumerate(time_ranges):
#     segments.append((file_id, start, None, end, idx))

# 并发处理
with ThreadPoolExecutor(max_workers=4) as executor:
    results = list(executor.map(lambda x: create_clip(*x), segments))

print(f"完成 {len([r for r in results if r])} 个切片")
```

### 示例 4: 自定义参数切片

```python
import requests

BASE_URL = "http://localhost:8700"

# 高质量切片（用于预览）
response = requests.get(f"{BASE_URL}/clip", params={
    "file_id": "your_file_id",
    "start": 0,
    "duration": 10,
    "return_type": "url",
    "scale": "1280:-1",  # 720p
    "fps": 30,           # 30帧/秒
    "crf": 23,           # 更高质量
    "preset": "medium"   # 平衡速度和质量
})

# 低质量切片（用于VLM快速分析）
response = requests.get(f"{BASE_URL}/clip", params={
    "file_id": "your_file_id",
    "start": 0,
    "duration": 10,
    "return_type": "url",
    "scale": "320:-1",   # 320p
    "fps": 5,            # 5帧/秒
    "crf": 35,           # 较低质量
    "preset": "ultrafast"
})
```

### 示例 5: 监控和管理

```python
import requests
import time

BASE_URL = "http://localhost:8700"

def get_storage_stats():
    """获取存储统计"""
    response = requests.get(f"{BASE_URL}/stats")
    if response.status_code == 200:
        data = response.json()
        print(f"上传文件: {data['uploads']['count']} 个 ({data['uploads']['size_mb']} MB)")
        print(f"切片文件: {data['segments']['count']} 个 ({data['segments']['size_mb']} MB)")
        print(f"总大小: {data['total_size_mb']} MB")
        return data
    return None

def cleanup_old_files(hours: int = 2):
    """手动清理旧文件"""
    response = requests.delete(f"{BASE_URL}/cleanup", params={"hours": hours})
    if response.status_code == 200:
        data = response.json()
        print(f"清理完成: 删除 {data['deleted_count']} 个文件，释放 {data['freed_space_mb']} MB")
        return data
    return None

# 使用示例
print("=== 当前存储状态 ===")
get_storage_stats()

print("\n=== 清理3小时前的文件 ===")
cleanup_old_files(hours=3)

print("\n=== 清理后的存储状态 ===")
get_storage_stats()
```

---

## cURL 示例

### 上传视频
```bash
curl -X POST "http://localhost:8700/upload" \
  -F "file=@video.mp4"
```

### 获取视频信息
```bash
curl "http://localhost:8700/video/abc123"
```

### 切片视频（使用持续时间，返回文件）
```bash
curl "http://localhost:8700/clip?file_id=abc123&start=10&duration=5&return_type=file" \
  --output clip.mp4
```

### 切片视频（使用起止时间，返回文件）
```bash
curl "http://localhost:8700/clip?file_id=abc123&start=10&end=15&return_type=file" \
  --output clip.mp4
```

### 切片视频（使用持续时间，返回URL）
```bash
curl "http://localhost:8700/clip?file_id=abc123&start=10&duration=5&return_type=url"
```

### 切片视频（使用起止时间，返回URL）
```bash
curl "http://localhost:8700/clip?file_id=abc123&start=10&end=15&return_type=url"
```

### 获取统计信息
```bash
curl "http://localhost:8700/stats"
```

### 手动清理
```bash
curl -X DELETE "http://localhost:8700/cleanup?hours=2"
```

---

## JavaScript/Node.js 示例

```javascript
const axios = require('axios');
const FormData = require('form-data');
const fs = require('fs');

const BASE_URL = 'http://localhost:8700';

// 上传视频
async function uploadVideo(filePath) {
  const formData = new FormData();
  formData.append('file', fs.createReadStream(filePath));
  
  const response = await axios.post(`${BASE_URL}/upload`, formData, {
    headers: formData.getHeaders()
  });
  
  const data = response.data;
  console.log('File ID:', data.file_id);
  console.log('视频信息:', data.video_info);
  
  return data;
}

// 获取视频信息
async function getVideoInfo(fileId) {
  const response = await axios.get(`${BASE_URL}/video/${fileId}`);
  return response.data;
}

// 获取切片URL（支持两种时间方式）
async function getClipUrl(fileId, start, options = {}) {
  const params = {
    file_id: fileId,
    start: start,
    return_type: 'url'
  };
  
  // 方式1：使用持续时间
  if (options.duration !== undefined) {
    params.duration = options.duration;
  }
  // 方式2：使用结束时间
  else if (options.end !== undefined) {
    params.end = options.end;
  }
  else {
    throw new Error('必须提供 duration 或 end 参数之一');
  }
  
  const response = await axios.get(`${BASE_URL}/clip`, { params });
  return response.data.url;
}

// 使用示例
(async () => {
  try {
    // 上传视频并获取信息
    const uploadData = await uploadVideo('video.mp4');
    const fileId = uploadData.file_id;
    const videoInfo = uploadData.video_info;
    
    console.log(`视频时长: ${videoInfo.duration}秒`);
    console.log(`分辨率: ${videoInfo.width}x${videoInfo.height}`);
    console.log(`帧率: ${videoInfo.fps} fps`);
    
    // 方式1：使用持续时间
    const clipUrl1 = await getClipUrl(fileId, 10, { duration: 5 });
    console.log('Clip URL (10秒开始，持续5秒):', clipUrl1);
    
    // 方式2：使用起止时间
    const clipUrl2 = await getClipUrl(fileId, 10, { end: 15 });
    console.log('Clip URL (10秒到15秒):', clipUrl2);
    
    // 查询视频信息
    const info = await getVideoInfo(fileId);
    console.log('视频详细信息:', info.video_info);
  } catch (error) {
    console.error('Error:', error.message);
  }
})();
```

---

## 运行测试脚本

```bash
python test_api.py
```

测试脚本会引导你完成：
1. 上传视频
2. 切片测试（文件和URL模式）
3. 查看统计信息
4. 手动清理测试

---

## 常见问题

### Q: 如何修改清理时间？
A: 编辑 `config.py` 文件：
```python
CLEANUP_INTERVAL_HOURS = 1  # 每隔多少小时清理一次
FILE_EXPIRY_HOURS = 2       # 清理多少小时前的文件
```

### Q: 如何保留原始上传文件不被清理？
A: 编辑 `app.py` 中的 `cleanup_old_files` 函数，注释掉清理上传文件的部分：
```python
# 清理上传文件（可选，根据需求决定是否清理原始视频）
# for file_path in UPLOAD_DIR.glob("*"):
#     ...
```

### Q: 如何调整默认视频参数？
A: 编辑 `config.py` 文件：
```python
DEFAULT_SCALE = "720:-1"    # 改为720p
DEFAULT_FPS = 15            # 改为15帧/秒
DEFAULT_CRF = 25            # 改为更高质量
```

### Q: 切片失败怎么办？
A: 检查：
1. FFmpeg 是否正确安装：`ffmpeg -version`
2. 查看日志输出的错误信息
3. 确认视频文件格式是否支持
4. 检查磁盘空间是否充足


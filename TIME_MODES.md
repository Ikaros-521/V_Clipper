# 切片时间参数说明

视频切片接口支持两种时间指定方式，可以根据使用场景灵活选择。

## 📋 两种时间方式对比

| 方式 | 参数组合 | 适用场景 | 示例 |
|------|---------|---------|------|
| **持续时间模式** | `start` + `duration` | 知道起点和持续时长 | 从第10秒开始，截取5秒 |
| **起止时间模式** | `start` + `end` | 知道起点和终点 | 从第10秒到第15秒 |

## 🎯 方式1: 持续时间模式 (start + duration)

### 适用场景
- ✅ 需要固定时长的片段（如每5秒一段）
- ✅ 批量切片时保持统一时长
- ✅ 不关心结束时间点，只关心持续多久

### 参数说明
- `start`: 起始时间（秒）
- `duration`: 持续时间（秒）

### 使用示例

**Python:**
```python
import requests

response = requests.get("http://localhost:8700/clip", params={
    "file_id": "abc123",
    "start": 10,        # 从第10秒开始
    "duration": 5,      # 持续5秒
    "return_type": "url"
})
# 结果：10秒 - 15秒的视频片段
```

**cURL:**
```bash
curl "http://localhost:8700/clip?file_id=abc123&start=10&duration=5&return_type=url"
```

**JavaScript:**
```javascript
const response = await axios.get('http://localhost:8700/clip', {
  params: {
    file_id: 'abc123',
    start: 10,
    duration: 5,
    return_type: 'url'
  }
});
```

### 响应示例
```json
{
  "url": "http://localhost:8700/media/abc123_10_5_480_-1_10.mp4",
  "filename": "abc123_10_5_480_-1_10.mp4",
  "file_id": "abc123",
  "start": 10,
  "duration": 5,
  "size_bytes": 524288
}
```

---

## 🎯 方式2: 起止时间模式 (start + end)

### 适用场景
- ✅ 明确知道开始和结束的时间点
- ✅ 从时间轴上选择特定区间
- ✅ 更直观的时间范围表达

### 参数说明
- `start`: 起始时间（秒）
- `end`: 结束时间（秒）

### 使用示例

**Python:**
```python
import requests

response = requests.get("http://localhost:8700/clip", params={
    "file_id": "abc123",
    "start": 10,        # 从第10秒开始
    "end": 15,          # 到第15秒结束
    "return_type": "url"
})
# 结果：10秒 - 15秒的视频片段（持续5秒）
```

**cURL:**
```bash
curl "http://localhost:8700/clip?file_id=abc123&start=10&end=15&return_type=url"
```

**JavaScript:**
```javascript
const response = await axios.get('http://localhost:8700/clip', {
  params: {
    file_id: 'abc123',
    start: 10,
    end: 15,
    return_type: 'url'
  }
});
```

### 响应示例
```json
{
  "url": "http://localhost:8700/media/abc123_10_5_480_-1_10.mp4",
  "filename": "abc123_10_5_480_-1_10.mp4",
  "file_id": "abc123",
  "start": 10,
  "duration": 5,
  "end": 15,
  "size_bytes": 524288
}
```

---

## ⚠️ 参数验证规则

### 1. 必须提供其中一种方式
```python
# ❌ 错误：两个都不提供
requests.get("/clip", params={"file_id": "abc", "start": 10})
# 错误信息：必须提供 duration（持续时间）或 end（结束时间）参数之一

# ✅ 正确：提供 duration
requests.get("/clip", params={"file_id": "abc", "start": 10, "duration": 5})

# ✅ 正确：提供 end
requests.get("/clip", params={"file_id": "abc", "start": 10, "end": 15})
```

### 2. 不能同时提供两种方式
```python
# ❌ 错误：同时提供 duration 和 end
requests.get("/clip", params={
    "file_id": "abc", 
    "start": 10, 
    "duration": 5,  # ❌
    "end": 15       # ❌
})
# 错误信息：duration 和 end 参数不能同时提供，请只使用其中一个
```

### 3. 时间值必须合法
```python
# ❌ 错误：end 必须大于 start
requests.get("/clip", params={"file_id": "abc", "start": 10, "end": 8})
# 错误信息：结束时间（8）必须大于起始时间（10）

# ❌ 错误：duration 必须大于 0
requests.get("/clip", params={"file_id": "abc", "start": 10, "duration": -5})
# 错误信息：持续时间（-5）必须大于0
```

---

## 💡 实际应用场景

### 场景1: 批量切片（固定时长）
使用 **持续时间模式** 更方便：

```python
# 将60秒视频切成12个5秒片段
file_id = "abc123"
for i in range(0, 60, 5):
    response = requests.get("/clip", params={
        "file_id": file_id,
        "start": i,
        "duration": 5,  # 每段固定5秒
        "return_type": "url"
    })
```

### 场景2: 精确时间区间
使用 **起止时间模式** 更直观：

```python
# 提取视频中的精彩片段
highlights = [
    (10.5, 25.3),   # 第一个精彩片段
    (45.2, 58.7),   # 第二个精彩片段
    (120.0, 135.5)  # 第三个精彩片段
]

for start, end in highlights:
    response = requests.get("/clip", params={
        "file_id": file_id,
        "start": start,
        "end": end,     # 直接使用起止时间
        "return_type": "url"
    })
```

### 场景3: VLM视频分析
两种方式都可以，根据数据来源选择：

```python
# 如果有时间戳对（如字幕时间轴）
subtitle_times = [(0, 5.2), (5.2, 10.8), (10.8, 15.3)]
for start, end in subtitle_times:
    clip_url = get_clip(file_id, start=start, end=end)
    analyze_with_vlm(clip_url)

# 如果需要固定间隔采样
for i in range(0, video_duration, 10):
    clip_url = get_clip(file_id, start=i, duration=10)
    analyze_with_vlm(clip_url)
```

---

## 🔄 两种方式的等价转换

```python
# 持续时间模式
start = 10
duration = 5
# 等价于
start = 10
end = 15

# 起止时间模式
start = 10
end = 15
# 等价于
start = 10
duration = 5  # end - start
```

---

## 📝 完整示例：封装通用函数

```python
import requests
from typing import Optional

BASE_URL = "http://localhost:8700"

def clip_video(
    file_id: str,
    start: float,
    duration: Optional[float] = None,
    end: Optional[float] = None,
    return_type: str = "url",
    **kwargs
):
    """
    通用视频切片函数，支持两种时间方式
    
    Args:
        file_id: 视频ID
        start: 起始时间（秒）
        duration: 持续时间（秒），与end二选一
        end: 结束时间（秒），与duration二选一
        return_type: 返回类型 "file" 或 "url"
        **kwargs: 其他参数（scale, fps, crf, preset等）
    
    Returns:
        如果return_type="url"，返回响应JSON
        如果return_type="file"，返回文件内容
    """
    if duration is None and end is None:
        raise ValueError("必须提供 duration 或 end 参数之一")
    
    if duration is not None and end is not None:
        raise ValueError("duration 和 end 不能同时提供")
    
    params = {
        "file_id": file_id,
        "start": start,
        "return_type": return_type,
        **kwargs
    }
    
    if duration is not None:
        params["duration"] = duration
    else:
        params["end"] = end
    
    response = requests.get(f"{BASE_URL}/clip", params=params)
    response.raise_for_status()
    
    if return_type == "url":
        return response.json()
    else:
        return response.content

# 使用示例
# 方式1：持续时间
result = clip_video("abc123", start=10, duration=5)
print(result["url"])

# 方式2：起止时间
result = clip_video("abc123", start=10, end=15)
print(result["url"])

# 下载文件
content = clip_video("abc123", start=10, duration=5, return_type="file")
with open("clip.mp4", "wb") as f:
    f.write(content)
```

---

## 🎓 总结

| 特性 | 持续时间模式 | 起止时间模式 |
|------|------------|------------|
| **参数** | start + duration | start + end |
| **计算方式** | 直接指定时长 | 自动计算时长 (end - start) |
| **适合场景** | 固定时长切片 | 精确时间区间 |
| **批量处理** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **直观性** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **灵活性** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |

**建议：**
- 批量处理、固定时长 → 使用 `start + duration`
- 精确区间、时间轴选择 → 使用 `start + end`
- 两种方式功能完全等价，选择最适合你的场景即可！


"""
V_Clipper API 测试脚本
演示如何使用视频切片服务
"""
import requests
import time

# 服务地址
BASE_URL = "http://localhost:8700"

def test_upload_video(video_path: str):
    """测试上传视频"""
    print(f"\n=== 测试上传视频 ===")
    with open(video_path, "rb") as f:
        response = requests.post(f"{BASE_URL}/upload", files={"file": f})
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 上传成功")
        print(f"   File ID: {data['file_id']}")
        print(f"   Filename: {data['filename']}")
        return data['file_id']
    else:
        print(f"❌ 上传失败: {response.text}")
        return None

def test_clip_video_file(file_id: str, start: float, duration: float = None, end: float = None):
    """测试切片视频（返回文件）"""
    print(f"\n=== 测试切片视频（返回文件）===")
    params = {
        "file_id": file_id,
        "start": start,
        "return_type": "file"
    }
    
    if duration is not None:
        params["duration"] = duration
        time_desc = f"{start}秒开始，持续{duration}秒"
    elif end is not None:
        params["end"] = end
        time_desc = f"{start}秒到{end}秒"
    else:
        print("❌ 必须提供 duration 或 end 参数之一")
        return None
    
    print(f"   时间范围: {time_desc}")
    response = requests.get(f"{BASE_URL}/clip", params=params)
    
    if response.status_code == 200:
        output_file = f"test_clip_{start}_{duration or (end-start)}.mp4"
        with open(output_file, "wb") as f:
            f.write(response.content)
        print(f"✅ 切片成功，已保存到: {output_file}")
        print(f"   文件大小: {len(response.content) / 1024:.2f} KB")
        return output_file
    else:
        print(f"❌ 切片失败: {response.text}")
        return None

def test_clip_video_url(file_id: str, start: float, duration: float = None, end: float = None):
    """测试切片视频（返回URL）"""
    print(f"\n=== 测试切片视频（返回URL）===")
    params = {
        "file_id": file_id,
        "start": start,
        "return_type": "url"
    }
    
    if duration is not None:
        params["duration"] = duration
        time_desc = f"{start}秒开始，持续{duration}秒"
    elif end is not None:
        params["end"] = end
        time_desc = f"{start}秒到{end}秒"
    else:
        print("❌ 必须提供 duration 或 end 参数之一")
        return None
    
    print(f"   时间范围: {time_desc}")
    response = requests.get(f"{BASE_URL}/clip", params=params)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 切片成功")
        print(f"   URL: {data['url']}")
        print(f"   Filename: {data['filename']}")
        print(f"   Size: {data.get('size_bytes', 0) / 1024:.2f} KB")
        if 'end' in data:
            print(f"   时间: {data['start']}s - {data['end']}s (持续{data['duration']}s)")
        else:
            print(f"   时间: {data['start']}s 开始，持续 {data['duration']}s")
        return data['url']
    else:
        print(f"❌ 切片失败: {response.text}")
        return None

def test_get_stats():
    """测试获取统计信息"""
    print(f"\n=== 测试获取统计信息 ===")
    response = requests.get(f"{BASE_URL}/stats")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 获取成功")
        print(f"   上传文件: {data['uploads']['count']} 个, {data['uploads']['size_mb']} MB")
        print(f"   切片文件: {data['segments']['count']} 个, {data['segments']['size_mb']} MB")
        print(f"   总大小: {data['total_size_mb']} MB")
        print(f"   清理配置: 每 {data['cleanup_config']['interval_hours']} 小时清理 {data['cleanup_config']['expiry_hours']} 小时前的文件")
        return data
    else:
        print(f"❌ 获取失败: {response.text}")
        return None

def test_manual_cleanup(hours: int = 2):
    """测试手动清理"""
    print(f"\n=== 测试手动清理（{hours}小时前的文件）===")
    response = requests.delete(f"{BASE_URL}/cleanup", params={"hours": hours})
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 清理成功")
        print(f"   删除文件数: {data['deleted_count']}")
        print(f"   释放空间: {data['freed_space_mb']} MB")
        return data
    else:
        print(f"❌ 清理失败: {response.text}")
        return None

def main():
    """主测试流程"""
    print("=" * 60)
    print("V_Clipper API 测试")
    print("=" * 60)
    
    # 检查服务是否运行
    try:
        response = requests.get(f"{BASE_URL}/docs")
        if response.status_code != 200:
            print("❌ 服务未运行，请先启动服务: python app.py")
            return
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务，请先启动服务: python app.py")
        return
    
    print("✅ 服务正在运行")
    
    # 测试上传（需要提供实际的视频文件路径）
    video_path = input("\n请输入要测试的视频文件路径（或按回车跳过上传测试）: ").strip()
    
    if video_path:
        file_id = test_upload_video(video_path)
        
        if file_id:
            # 测试切片（使用持续时间）
            test_clip_video_file(file_id, start=0, duration=5)
            
            # 测试切片（使用起止时间）
            test_clip_video_file(file_id, start=5, end=10)
            
            # 测试切片URL（使用持续时间）
            test_clip_video_url(file_id, start=10, duration=5)
            
            # 测试切片URL（使用起止时间）
            test_clip_video_url(file_id, start=15, end=20)
    else:
        print("\n⏭️  跳过上传和切片测试")
    
    # 测试统计信息
    test_get_stats()
    
    # 询问是否测试清理
    cleanup_test = input("\n是否测试手动清理功能？(y/n): ").strip().lower()
    if cleanup_test == 'y':
        hours = input("清理多少小时前的文件？(默认2): ").strip()
        hours = int(hours) if hours else 2
        test_manual_cleanup(hours)
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
    print(f"\n📖 API文档: {BASE_URL}/docs")
    print(f"📊 统计信息: {BASE_URL}/stats")

if __name__ == "__main__":
    main()


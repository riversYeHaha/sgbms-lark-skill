# ffmpeg 截图命令参考

## 基本截图

### 从视频指定时间点截图

```bash
# 在 15分30秒处截图
ffmpeg -ss 00:15:30 -i input.mp4 -vframes 1 -q:v 2 output.jpg

# 使用秒数
ffmpeg -ss 930 -i input.mp4 -vframes 1 -q:v 2 output.jpg
```

### 参数说明

| 参数 | 说明 |
|------|------|
| `-ss` | 开始时间（支持 HH:MM:SS 或秒数） |
| `-i` | 输入文件 |
| `-vframes 1` | 只截取一帧 |
| `-q:v 2` | 质量（1-31，1 最好） |

## 批量截图

### 根据时间列表截图

```bash
#!/bin/bash
# screenshots.sh

times=("00:05:00" "00:10:30" "00:15:00" "00:20:00")
video="meeting.mp4"
output_dir="./screenshots"

mkdir -p $output_dir

for i in "${!times[@]}"; do
  ffmpeg -ss "${times[$i]}" -i "$video" -vframes 1 -q:v 2 \
    "$output_dir/screenshot_$i.jpg"
done
```

### Python 批量截图

```python
import subprocess
import json

def capture_screenshots(video_path, timestamps, output_dir):
    """
    根据时间戳列表截取视频关键帧
    
    Args:
        video_path: 视频文件路径
        timestamps: 时间戳列表 ["00:05:00", "00:10:00"]
        output_dir: 输出目录
    """
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    screenshots = []
    for i, ts in enumerate(timestamps):
        output_path = f"{output_dir}/screenshot_{i:03d}.jpg"
        
        cmd = [
            'ffmpeg',
            '-ss', ts,
            '-i', video_path,
            '-vframes', '1',
            '-q:v', '2',
            '-y',  # 覆盖已存在文件
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            screenshots.append({
                'index': i,
                'timestamp': ts,
                'path': output_path
            })
        else:
            print(f"截图失败 {ts}: {result.stderr}")
    
    return screenshots

# 使用示例
if __name__ == "__main__":
    video = "./meeting.mp4"
    times = ["00:05:00", "00:10:30", "00:15:00"]
    output = "./screenshots"
    
    results = capture_screenshots(video, times, output)
    print(json.dumps(results, indent=2, ensure_ascii=False))
```

## 高级截图

### 指定分辨率截图

```bash
# 截图并调整大小
ffmpeg -ss 00:10:00 -i input.mp4 -vframes 1 -q:v 2 \
  -vf "scale=1920:1080" output.jpg
```

### 截图并添加时间戳水印

```bash
ffmpeg -ss 00:10:00 -i input.mp4 -vframes 1 -q:v 2 \
  -vf "drawtext=text='10:00':fontsize=48:fontcolor=white:x=20:y=20" \
  output.jpg
```

### 从 URL 截图（先下载）

```python
import requests
import subprocess
import tempfile
import os

def capture_from_url(video_url, timestamp, output_path):
    """从视频 URL 截图"""
    
    # 下载视频到临时文件
    response = requests.get(video_url, stream=True)
    
    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp:
        for chunk in response.iter_content(chunk_size=8192):
            tmp.write(chunk)
        tmp_path = tmp.name
    
    try:
        # 截图
        cmd = [
            'ffmpeg',
            '-ss', timestamp,
            '-i', tmp_path,
            '-vframes', '1',
            '-q:v', '2',
            '-y',
            output_path
        ]
        subprocess.run(cmd, check=True)
        
    finally:
        # 清理临时文件
        os.unlink(tmp_path)
    
    return output_path
```

## 检查视频信息

```bash
# 获取视频时长、分辨率等信息
ffmpeg -i input.mp4 2>&1 | grep -E "Duration|Stream"

# 或使用 ffprobe
ffprobe -v quiet -print_format json -show_format -show_streams input.mp4
```

## 常见错误处理

### 截图黑屏

如果截图是黑屏，可能是时间点问题，尝试：

```bash
# 在 -ss 前添加 -accurate_seek
ffmpeg -ss 00:10:00 -accurate_seek -i input.mp4 -vframes 1 output.jpg

# 或先复制关键帧
ffmpeg -ss 00:10:00 -i input.mp4 -vframes 1 -q:v 2 -vf "select=eq(pict_type\,I)" output.jpg
```

### 视频无法解码

```bash
# 指定解码器
ffmpeg -c:v h264 -ss 00:10:00 -i input.mp4 -vframes 1 output.jpg
```

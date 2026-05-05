#!/usr/bin/env python3
"""智能截图 — 根据脚本标记下载视频并用 ffmpeg 截取关键帧"""
import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


def capture_screenshots(meeting_id, script, output_dir):
    screenshots = []
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    video_path = download_meeting_video(meeting_id)
    
    if not video_path or not os.path.exists(video_path):
        return screenshots
    
    for scene in script.get('scenes', []):
        if scene.get('type') != 'screenshot':
            continue
        
        screenshot_config = scene.get('screenshot', {})
        if not screenshot_config.get('needed'):
            continue
        
        timestamp = screenshot_config.get('timestamp', '00:00:00')
        scene_id = scene['scene_id']
        
        screenshot_file = output_path / f"screenshot_{scene_id:03d}.jpg"
        
        cmd = [
            'ffmpeg',
            '-ss', timestamp,
            '-i', video_path,
            '-vframes', '1',
            '-q:v', '2',
            '-y',
            str(screenshot_file)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            screenshot_config['path'] = str(screenshot_file)
            screenshots.append({
                'scene_id': scene_id,
                'timestamp': timestamp,
                'path': str(screenshot_file)
            })
    
    return screenshots


def download_meeting_video(meeting_id, tmp_dir=None):
    if tmp_dir is None:
        tmp_dir = Path('./tmp')
    else:
        tmp_dir = Path(tmp_dir)
    tmp_dir.mkdir(exist_ok=True)
    
    video_path = tmp_dir / f"meeting_{meeting_id}.mp4"
    
    if video_path.exists():
        return str(video_path)
    
    # Check ffmpeg availability
    if not shutil.which('ffmpeg'):
        print("警告: ffmpeg 未安装，跳过视频处理", file=sys.stderr)
        return None
    
    cmd = ['lark-cli', 'vc', '+recording',
           '--meeting-ids', meeting_id,
           '--output-dir', str(tmp_dir)]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        # vc +recording may place files in subdirectories; find the mp4
        for root, dirs, files in os.walk(tmp_dir):
            for f in files:
                if f.endswith('.mp4'):
                    return str(Path(root) / f)
    
    return None


def main():
    parser = argparse.ArgumentParser(description='截取会议视频关键帧')
    parser.add_argument('--meeting-id', required=True, help='会议 ID')
    parser.add_argument('--script', required=True, help='脚本 JSON 文件路径')
    parser.add_argument('--output-dir', default='./screenshots', help='截图输出目录')
    parser.add_argument('--tmp-dir', default='./tmp', help='临时文件目录')
    
    args = parser.parse_args()
    
    with open(args.script, 'r', encoding='utf-8') as f:
        script = json.load(f)
    
    screenshots = capture_screenshots(args.meeting_id, script, args.output_dir)
    
    print(f"截图完成: {len(screenshots)} 张")
    for s in screenshots:
        print(f"  [{s['timestamp']}] -> {s['path']}")
    
    if screenshots:
        # Save updated script with paths
        output_script = Path(args.output_dir) / 'script_with_screenshots.json'
        with open(output_script, 'w', encoding='utf-8') as f:
            json.dump(script, f, ensure_ascii=False, indent=2)
        print(f"已更新脚本: {output_script}")


if __name__ == '__main__':
    main()

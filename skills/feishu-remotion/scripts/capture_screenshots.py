#!/usr/bin/env python3
import json
import os
import subprocess
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


def download_meeting_video(meeting_id):
    tmp_dir = Path('./tmp')
    tmp_dir.mkdir(exist_ok=True)
    
    video_path = tmp_dir / f"meeting_{meeting_id}.mp4"
    
    if video_path.exists():
        return str(video_path)
    
    cmd = ['lark-cli', 'vc', '+recording',
           '--meeting-id', meeting_id,
           '--output', str(video_path)]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0 and video_path.exists():
        return str(video_path)
    
    return None

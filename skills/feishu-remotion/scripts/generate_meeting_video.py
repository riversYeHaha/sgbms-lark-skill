#!/usr/bin/env python3
"""
飞书会议视频生成主脚本
整合所有步骤，一键生成会议总结视频
"""

import argparse
import json
import os
import sys
import subprocess
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from get_meeting_info import get_meeting_by_link
from get_meeting_minutes import get_meeting_minutes
from generate_script import generate_script
from capture_screenshots import capture_screenshots
from render_video import render_video


def load_config(config_path):
    try:
        import yaml
        with open(config_path, 'r', encoding='utf-8') as f:
            raw = f.read()
        for env_var, value in os.environ.items():
            raw = raw.replace(f'${{{env_var}}}', value)
        return yaml.safe_load(raw)
    except FileNotFoundError:
        return {}
    except ImportError:
        print("提示: 安装 pyyaml 以使用配置文件: pip install pyyaml")
        return {}


def merge_config(args, config):
    if not config:
        return
    if not args.duration and config.get('video', {}).get('max_duration'):
        args.duration = config['video']['max_duration']
    ffmpeg_path = config.get('ffmpeg', {}).get('path', 'ffmpeg')
    os.environ.setdefault('FFMPEG_PATH', ffmpeg_path)


def main():
    parser = argparse.ArgumentParser(description='生成飞书会议总结视频')
    parser.add_argument('--meeting-link', help='会议链接')
    parser.add_argument('--date', help='查询日程日期 (YYYY-MM-DD)')
    parser.add_argument('--output-dir', default='./output', help='输出目录')
    parser.add_argument('--style', default='summary', 
                       choices=['summary', 'detailed', 'quick'],
                       help='视频风格')
    parser.add_argument('--duration', type=int, default=0,
                       help='最大时长（秒），0=使用默认值')
    parser.add_argument('--provider', default='deepseek',
                       choices=['deepseek', 'kimi', 'glm', 'volcengine'],
                       help='LLM 提供商')
    parser.add_argument('--config', default='./config.yaml',
                       help='配置文件路径')
    parser.add_argument('--skip-screenshots', action='store_true',
                       help='跳过截图步骤')
    
    args = parser.parse_args()
    
    config = load_config(args.config)
    merge_config(args, config)
    
    if args.duration <= 0:
        args.duration = 180
    
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    tmp_dir = output_dir / 'tmp'
    tmp_dir.mkdir(exist_ok=True)
    
    print("=" * 60)
    print("飞书会议视频生成")
    print("=" * 60)
    
    print("\n[1/5] 获取会议信息...")
    if args.meeting_link:
        meeting_info = get_meeting_by_link(args.meeting_link)
    elif args.date:
        print(f"查询 {args.date} 的日程...")
        meeting_info = query_schedule(args.date)
    else:
        print("错误：请提供会议链接或日期")
        sys.exit(1)
    
    meeting_id = meeting_info['meeting_id']
    print(f"  会议: {meeting_info['topic']}")
    print(f"  ID: {meeting_id}")
    
    with open(tmp_dir / 'meeting.json', 'w', encoding='utf-8') as f:
        json.dump(meeting_info, f, ensure_ascii=False, indent=2)
    
    print("\n[2/5] 获取妙记和逐字稿...")
    minutes = get_meeting_minutes(meeting_id)
    
    if not minutes:
        print("  警告：未找到妙记，使用会议基本信息生成")
        minutes = {
            'meeting_id': meeting_id,
            'transcript': [],
            'summary': meeting_info.get('topic', '会议总结')
        }
    
    with open(tmp_dir / 'transcript.json', 'w', encoding='utf-8') as f:
        json.dump(minutes, f, ensure_ascii=False, indent=2)
    
    print(f"  逐字稿长度: {len(minutes.get('transcript', []))} 条")
    
    print("\n[3/5] 生成精炼脚本...")
    script = generate_script(
        transcript=minutes,
        style=args.style,
        max_duration=args.duration,
        provider=args.provider
    )
    
    with open(tmp_dir / 'script.json', 'w', encoding='utf-8') as f:
        json.dump(script, f, ensure_ascii=False, indent=2)
    
    print(f"  脚本场景数: {len(script['scenes'])}")
    print(f"  预计时长: {script['metadata']['duration_seconds']} 秒")
    
    screenshots_dir = tmp_dir / 'screenshots'
    if not args.skip_screenshots:
        print("\n[4/5] 截取关键帧...")
        screenshots = capture_screenshots(
            meeting_id=meeting_id,
            script=script,
            output_dir=screenshots_dir
        )
        print(f"  截图数量: {len(screenshots)}")
    else:
        print("\n[4/5] 跳过截图...")
        screenshots_dir.mkdir(exist_ok=True)
    
    print("\n[5/5] 生成 Remotion 视频...")
    output_video = output_dir / f"meeting-summary-{meeting_id}.mp4"
    
    render_video(
        script=script,
        screenshots_dir=screenshots_dir,
        output_path=output_video
    )
    
    print(f"\n{'=' * 60}")
    print(f"视频生成完成!")
    print(f"输出: {output_video}")
    print(f"{'=' * 60}")


def query_schedule(date):
    cmd = ['lark-cli', 'calendar', '+agenda',
           '--date', date, '--format', 'json']
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"查询日程失败: {result.stderr}")
        sys.exit(1)
    
    schedule = json.loads(result.stdout)
    
    for event in schedule.get('events', []):
        if event.get('meeting_link'):
            return {
                'meeting_id': event['meeting_link'].split('/')[-1],
                'topic': event['summary'],
                'start_time': event['start_time'],
                'end_time': event['end_time']
            }
    
    print("未找到有会议链接的日程")
    sys.exit(1)


if __name__ == '__main__':
    main()

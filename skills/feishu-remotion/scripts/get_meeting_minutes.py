#!/usr/bin/env python3
"""获取飞书会议妙记和逐字稿"""
import argparse
import json
import subprocess
import sys
from pathlib import Path


def get_meeting_minutes(meeting_id):
    search_cmd = ['lark-cli', 'minutes', '+search',
                  '--query', meeting_id,
                  '--format', 'json']
    
    result = subprocess.run(search_cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        return None
    
    search_result = json.loads(result.stdout)
    
    if not search_result.get('items'):
        return None
    
    minutes_id = search_result['items'][0]['minutes_id']
    
    detail_cmd = ['lark-cli', 'minutes', '+detail',
                  '--minutes-id', minutes_id,
                  '--format', 'json']
    
    detail_result = subprocess.run(detail_cmd, capture_output=True, text=True)
    
    if detail_result.returncode != 0:
        return None
    
    detail = json.loads(detail_result.stdout)
    
    transcript = []
    for segment in detail.get('transcript', []):
        transcript.append({
            'speaker': segment.get('speaker', '未知'),
            'start_time': segment.get('start_time', ''),
            'end_time': segment.get('end_time', ''),
            'text': segment.get('text', '')
        })
    
    return {
        'meeting_id': meeting_id,
        'minutes_id': minutes_id,
        'transcript': transcript,
        'summary': detail.get('summary', ''),
        'video_url': detail.get('video_url', '')
    }


def main():
    parser = argparse.ArgumentParser(description='获取飞书会议妙记和逐字稿')
    parser.add_argument('--meeting-id', required=True, help='会议 ID')
    parser.add_argument('--output', '-o', help='输出文件路径 (JSON)')
    
    args = parser.parse_args()
    
    minutes = get_meeting_minutes(args.meeting_id)
    
    if not minutes:
        print(f"错误：未找到会议 {args.meeting_id} 的妙记", file=sys.stderr)
        sys.exit(1)
    
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(minutes, f, ensure_ascii=False, indent=2)
        print(f"逐字稿已保存到: {args.output}")
    else:
        print(json.dumps(minutes, ensure_ascii=False, indent=2))
    
    print(f"逐字稿条数: {len(minutes.get('transcript', []))}")


if __name__ == '__main__':
    main()

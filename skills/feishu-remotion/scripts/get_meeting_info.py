#!/usr/bin/env python3
"""获取飞书会议信息 — 通过会议链接查询会议详情"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


def get_meeting_by_link(meeting_link):
    meeting_id = extract_meeting_id(meeting_link)
    
    cmd = ['lark-cli', 'vc', '+detail', 
           '--meeting-id', meeting_id, 
           '--format', 'json']
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        return {
            'meeting_id': meeting_id,
            'topic': '未知会议',
            'start_time': '',
            'end_time': '',
            'organizer': '',
            'participants': [],
            'has_recording': False,
            'has_minutes': False
        }
    
    data = json.loads(result.stdout)
    
    return {
        'meeting_id': meeting_id,
        'topic': data.get('topic', '未知会议'),
        'start_time': data.get('start_time', ''),
        'end_time': data.get('end_time', ''),
        'organizer': data.get('organizer', ''),
        'participants': data.get('participants', []),
        'has_recording': data.get('has_recording', False),
        'has_minutes': data.get('has_minutes', False)
    }


def extract_meeting_id(link):
    patterns = [
        r'/j/(\d+)',
        r'/s/(\d+)',
        r'meeting_id=(\d+)',
        r'/(\d+)$'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, link)
        if match:
            return match.group(1)
    
    return link.split('/')[-1]


def main():
    parser = argparse.ArgumentParser(description='获取飞书会议信息')
    parser.add_argument('--meeting-link', required=True, help='会议链接')
    parser.add_argument('--output', '-o', help='输出文件路径 (JSON)')
    
    args = parser.parse_args()
    
    result = get_meeting_by_link(args.meeting_link)
    
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"会议信息已保存到: {args.output}")
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()

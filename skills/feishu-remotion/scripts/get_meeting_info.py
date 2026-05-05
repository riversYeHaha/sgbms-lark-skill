#!/usr/bin/env python3
import json
import re
import subprocess


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

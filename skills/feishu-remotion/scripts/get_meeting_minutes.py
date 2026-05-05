#!/usr/bin/env python3
import json
import subprocess


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

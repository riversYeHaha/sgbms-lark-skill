#!/usr/bin/env python3
import json
import os
from openai import OpenAI


def generate_script(transcript, style='summary', max_duration=180):
    full_text = '\n'.join([
        f"[{seg['speaker']}] {seg['text']}"
        for seg in transcript.get('transcript', [])
    ])
    
    summary = transcript.get('summary', '')
    
    prompt = f"""请将以下会议逐字稿转换为视频脚本，用于生成会议总结视频。

会议摘要：
{summary}

逐字稿：
{full_text[:5000]}

要求：
- 风格：{style}
- 最大时长：{max_duration} 秒
- 输出 JSON 格式，符合以下结构：

{{
  "version": "1.0",
  "metadata": {{
    "title": "会议标题",
    "duration_seconds": 180,
    "style": "{style}",
    "total_scenes": 5
  }},
  "scenes": [
    {{
      "scene_id": 1,
      "type": "title",
      "title": "会议标题",
      "subtitle": "日期",
      "duration": 3,
      "visual": {{"type": "title_card", "animation": "scale_up"}}
    }},
    {{
      "scene_id": 2,
      "type": "content",
      "content": "核心要点",
      "bullet_points": ["要点1", "要点2"],
      "duration": 8,
      "visual": {{"type": "bullet_points", "animation": "typewriter"}}
    }},
    {{
      "scene_id": 3,
      "type": "screenshot",
      "content": "需要截图说明的内容",
      "screenshot": {{
        "needed": true,
        "timestamp": "00:10:00",
        "caption": "说明"
      }},
      "duration": 6,
      "visual": {{"type": "image_show", "animation": "zoom_in"}}
    }}
  ]
}}

场景类型：title, content, screenshot, speaker, ending
视觉类型：title_card, bullet_points, image_show, quote_card, ending_card
动画：typewriter, fade_in, slide_in, zoom_in, scale_up

请确保：
1. 总时长不超过 {max_duration} 秒
2. 每个场景有明确的 duration
3. screenshot 场景标记 needed: true 和合理的 timestamp
4. 内容精炼，适合视频展示
"""
    
    client = OpenAI(
        api_key=os.getenv('DEEPSEEK_API_KEY'),
        base_url='https://api.deepseek.com/v1'
    )
    
    response = client.chat.completions.create(
        model='deepseek-chat',
        messages=[
            {'role': 'system', 'content': '你是一个专业的会议视频脚本生成助手。'},
            {'role': 'user', 'content': prompt}
        ],
        temperature=0.7,
        max_tokens=4000
    )
    
    content = response.choices[0].message.content
    
    json_match = content.find('{')
    json_end = content.rfind('}') + 1
    
    if json_match >= 0 and json_end > json_match:
        script = json.loads(content[json_match:json_end])
    else:
        script = create_default_script(transcript, style, max_duration)
    
    return script


def create_default_script(transcript, style, max_duration):
    title = transcript.get('summary', '会议总结')[:20]
    
    scenes = [
        {
            'scene_id': 1,
            'type': 'title',
            'title': title,
            'subtitle': '会议总结',
            'duration': 3,
            'visual': {'type': 'title_card', 'animation': 'scale_up'}
        },
        {
            'scene_id': 2,
            'type': 'content',
            'content': '会议核心要点',
            'bullet_points': ['要点待补充'],
            'duration': 8,
            'visual': {'type': 'bullet_points', 'animation': 'typewriter'}
        },
        {
            'scene_id': 3,
            'type': 'ending',
            'content': '感谢参与',
            'duration': 3,
            'visual': {'type': 'ending_card', 'animation': 'fade_out'}
        }
    ]
    
    return {
        'version': '1.0',
        'metadata': {
            'title': title,
            'duration_seconds': 14,
            'style': style,
            'total_scenes': len(scenes)
        },
        'scenes': scenes
    }

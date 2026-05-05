#!/usr/bin/env python3
"""使用 LLM 将会议逐字稿提炼为视频脚本"""
import argparse
import json
import os
import sys
from pathlib import Path
from openai import OpenAI


# Multi-provider LLM configuration
LLM_PROVIDERS = {
    'deepseek': {
        'base_url': 'https://api.deepseek.com/v1',
        'model': 'deepseek-chat',
        'env_key': 'DEEPSEEK_API_KEY'
    },
    'kimi': {
        'base_url': 'https://api.moonshot.cn/v1',
        'model': 'moonshot-v1-32k',
        'env_key': 'MOONSHOT_API_KEY'
    },
    'glm': {
        'base_url': 'https://open.bigmodel.cn/api/paas/v4',
        'model': 'glm-4',
        'env_key': 'GLM_API_KEY'
    },
    'volcengine': {
        'base_url': 'https://ark.cn-beijing.volces.com/api/v3',
        'model': 'doubao-pro',
        'env_key': 'ARK_API_KEY'
    }
}


def get_llm_client(provider='deepseek', api_key=None):
    config = LLM_PROVIDERS.get(provider)
    if not config:
        raise ValueError(f"不支持的 LLM 提供商: {provider}. 可用: {list(LLM_PROVIDERS.keys())}")
    
    key = api_key or os.getenv(config['env_key'])
    if not key:
        raise ValueError(
            f"未设置 {config['env_key']} 环境变量，"
            f"请设置后重试或使用 --api-key 参数"
        )
    
    return OpenAI(api_key=key, base_url=config['base_url']), config['model']


def generate_script(transcript, style='summary', max_duration=180, provider='deepseek', api_key=None):
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
    
    client, model = get_llm_client(provider, api_key)
    
    response = client.chat.completions.create(
        model=model,
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


def main():
    parser = argparse.ArgumentParser(description='使用 LLM 生成会议视频脚本')
    parser.add_argument('--transcript', required=True, help='逐字稿 JSON 文件路径')
    parser.add_argument('--output', '-o', required=True, help='脚本输出路径')
    parser.add_argument('--style', default='summary', choices=['summary', 'detailed', 'quick'], help='视频风格')
    parser.add_argument('--max-duration', type=int, default=180, help='最大时长（秒）')
    parser.add_argument('--provider', default='deepseek', choices=list(LLM_PROVIDERS.keys()), help='LLM 提供商')
    parser.add_argument('--api-key', help='API Key（可选，默认读取环境变量）')
    
    args = parser.parse_args()
    
    try:
        with open(args.transcript, 'r', encoding='utf-8') as f:
            transcript = json.load(f)
    except FileNotFoundError:
        print(f"错误: 找不到文件 {args.transcript}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"错误: JSON 解析失败 - {e}", file=sys.stderr)
        sys.exit(1)
    
    script = generate_script(
        transcript=transcript,
        style=args.style,
        max_duration=args.max_duration,
        provider=args.provider,
        api_key=args.api_key
    )
    
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(script, f, ensure_ascii=False, indent=2)
    
    print(f"脚本已生成: {args.output}")
    print(f"  场景数: {len(script['scenes'])}")
    print(f"  预计时长: {script['metadata']['duration_seconds']} 秒")


if __name__ == '__main__':
    main()

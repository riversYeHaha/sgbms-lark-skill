#!/usr/bin/env python3
"""Generate Feishu Pet images via volcengine/wanxiang API."""

import argparse
import base64
import json
import os
from pathlib import Path

import requests

IMAGE_PROVIDERS = {
    "volcengine": {
        "base_url": "https://ark.cn-beijing.volces.com/api/v3",
        "models": ["doubao-seedream-5-0-260128"],
        "env_key": "ARK_API_KEY",
    },
    "wanxiang": {
        "base_url": "https://dashscope.aliyuncs.com/api/v1",
        "models": ["wan2.7-image-pro", "wan2.7-image"],
        "env_key": "DASHSCOPE_API_KEY",
    },
}

ALL_STATES = [
    "idle", "running-right", "running-left", "waving", "jumping",
    "failed", "waiting", "running", "review",
]


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def call_volcengine(model, api_key, prompt, input_images, output_path, size):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    data = {
        "model": model,
        "prompt": prompt,
        "sequential_image_generation": "disabled",
        "response_format": "url",
        "size": size,
        "stream": False,
        "watermark": True,
    }

    resp = requests.post(
        "https://ark.cn-beijing.volces.com/api/v3/images/generations",
        headers=headers,
        json=data,
        timeout=120,
    )
    resp.raise_for_status()
    result = resp.json()

    images = result.get("data", [])
    if not images:
        raise SystemExit(f"火山引擎 API 未返回图片: {json.dumps(result, ensure_ascii=False)[:500]}")

    img = images[0]
    if "b64_json" in img:
        raw = base64.b64decode(img["b64_json"])
    elif "url" in img:
        img_resp = requests.get(img["url"], timeout=60)
        img_resp.raise_for_status()
        raw = img_resp.content
    else:
        raise SystemExit(f"未知的响应格式: {json.dumps(img, ensure_ascii=False)[:200]}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(raw)
    return output_path


def call_wanxiang(model, api_key, prompt, input_images, output_path, size):
    """万相2.7 API — 文生图同步调用.

    Docs: https://help.aliyun.com/zh/model-studio/wan-image-generation-api-reference
    Endpoint: /services/aigc/multimodal-generation/generation
    Model: wan2.7-image-pro / wan2.7-image
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    content = [{"text": prompt}]
    for img_path in input_images:
        if img_path.exists():
            with open(img_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("utf-8")
            content.append({"image": f"data:image/png;base64,{b64}"})

    data = {
        "model": model,
        "input": {
            "messages": [{"role": "user", "content": content}],
        },
        "parameters": {
            "size": size,
            "n": 1,
            "watermark": False,
            "thinking_mode": True,
        },
    }

    resp = requests.post(
        "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation",
        headers=headers,
        json=data,
        timeout=180,
    )
    resp.raise_for_status()
    result = resp.json()

    choices = result.get("output", {}).get("choices", [])
    if not choices:
        raise SystemExit(f"万相 API 未返回图片: {json.dumps(result, ensure_ascii=False)[:500]}")

    for choice in choices:
        for item in choice.get("message", {}).get("content", []):
            if item.get("type") == "image" and item.get("image"):
                img_url = item["image"]
                img_resp = requests.get(img_url, timeout=60)
                img_resp.raise_for_status()
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_bytes(img_resp.content)
                return output_path

    raise SystemExit("万相 API 响应中未找到图片 URL")


def call_api(provider, model, api_key, prompt, input_images, output_path, size):
    if provider == "volcengine":
        return call_volcengine(model, api_key, prompt, input_images, output_path, size)
    elif provider == "wanxiang":
        return call_wanxiang(model, api_key, prompt, input_images, output_path, size)
    raise SystemExit(f"不支持的提供者: {provider}")


def generate_base(run_dir, provider, model, api_key):
    prompt_file = run_dir / "prompts" / "base.md"
    prompt = prompt_file.read_text(encoding="utf-8").strip()
    output_path = run_dir / "decoded" / "base.png"

    print(f"[generate] 生成基础形象 (model={model}, provider={provider})...")
    result = call_api(provider, model, api_key, prompt, [], output_path, "2K")
    print(f"[generate] 基础形象已保存: {result}")
    return result


def generate_row(run_dir, state, provider, model, api_key):
    prompt_file = run_dir / "prompts" / "rows" / f"{state}.md"

    manifest = load_json(run_dir / "imagegen-jobs.json")
    matching = [j for j in manifest.get("jobs", []) if j["id"] == state]
    frame_count = matching[0].get("frame_count", 6) if matching else 6

    prompt = prompt_file.read_text(encoding="utf-8").strip()
    output_path = run_dir / "decoded" / f"{state}.png"
    width = frame_count * 192
    height = 208
    size = f"{width}x{height}"

    print(f"[generate] 生成 {state} ({frame_count}帧, {size})...")
    result = call_api(provider, model, api_key, prompt, [], output_path, size)
    print(f"[generate] {state} 已保存: {result}")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True, help="运行目录")
    parser.add_argument("--provider", help="生图提供商 (volcengine/wanxiang)")
    parser.add_argument("--model", help="模型名称")
    parser.add_argument("--api-key", help="API Key (或设置环境变量 ARK_API_KEY / WANXIANG_API_KEY)")
    parser.add_argument("--states", required=True, help="base, idle, running-right, ... 或 all")
    args = parser.parse_args()

    run_dir = Path(args.run_dir).resolve()
    if not run_dir.exists():
        raise SystemExit(f"运行目录不存在: {run_dir}")

    pet_request = load_json(run_dir / "pet_request.json")
    provider = args.provider or pet_request.get("provider", "volcengine")

    info = IMAGE_PROVIDERS.get(provider)
    if not info:
        raise SystemExit(f"不支持的提供者: {provider}")

    model = args.model or info["models"][0]
    api_key = args.api_key or os.getenv(info["env_key"], "")
    if not api_key:
        raise SystemExit(
            f"未提供 API Key。通过 --api-key 传入或设置环境变量 {info['env_key']}"
        )

    states_raw = args.states.strip().lower()
    if states_raw == "all":
        states = ["base"] + ALL_STATES
    else:
        states = [s.strip() for s in states_raw.split(",")]

    for state in states:
        if state == "base":
            generate_base(run_dir, provider, model, api_key)
        else:
            generate_row(run_dir, state, provider, model, api_key)


if __name__ == "__main__":
    main()

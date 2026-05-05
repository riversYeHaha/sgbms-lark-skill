#!/usr/bin/env python3
"""Extract generated horizontal row strips into 192x208 sprite frames with chroma key removal."""

import argparse
import json
import math
import re
from pathlib import Path

from PIL import Image

CELL_WIDTH = 192
CELL_HEIGHT = 208
ROW_FRAME_COUNTS = {
    "idle": 6,
    "running-right": 8,
    "running-left": 8,
    "waving": 4,
    "jumping": 5,
    "failed": 8,
    "waiting": 6,
    "running": 6,
    "review": 6,
}


def parse_hex_color(value):
    if not re.fullmatch(r"#[0-9a-fA-F]{6}", value):
        raise SystemExit(f"无效的色度键颜色: {value}; 期望 #RRGGBB")
    return tuple(int(value[i : i + 2], 16) for i in (1, 3, 5))


def load_chroma_key(run_dir, override=None):
    if override:
        return parse_hex_color(override)
    request_path = run_dir / "pet_request.json"
    if request_path.is_file():
        request = json.loads(request_path.read_text(encoding="utf-8"))
        chroma_key = request.get("chroma_key")
        if isinstance(chroma_key, dict) and isinstance(chroma_key.get("hex"), str):
            return parse_hex_color(chroma_key["hex"])
    return parse_hex_color("#00FF00")


def color_distance(r, g, b, key):
    return math.sqrt((r - key[0]) ** 2 + (g - key[1]) ** 2 + (b - key[2]) ** 2)


def remove_chroma_background(image, chroma_key, threshold):
    rgba = image.convert("RGBA")
    pixels = rgba.load()
    for y in range(rgba.height):
        for x in range(rgba.width):
            r, g, b, a = pixels[x, y]
            if color_distance(r, g, b, chroma_key) <= threshold:
                pixels[x, y] = (r, g, b, 0)
    return rgba


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True, help="运行目录")
    parser.add_argument("--states", required=True, help="要提取的状态: idle, running-right, ... 或 all")
    parser.add_argument("--chroma-key", help="覆盖色度键颜色 (#RRGGBB)")
    parser.add_argument("--threshold", type=float, default=30, help="色度键距离阈值")
    args = parser.parse_args()

    run_dir = Path(args.run_dir).resolve()
    decoded_dir = run_dir / "decoded"
    frames_dir = run_dir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)

    chroma_key = load_chroma_key(run_dir, args.chroma_key)
    print(f"[extract] 色度键: #{chroma_key[0]:02x}{chroma_key[1]:02x}{chroma_key[2]:02x}, 阈值: {args.threshold}")

    states_raw = args.states.strip().lower()
    if states_raw == "all":
        states = list(ROW_FRAME_COUNTS.keys())
    else:
        states = [s.strip() for s in states_raw.split(",")]

    total_frames = 0
    for state in states:
        if state not in ROW_FRAME_COUNTS:
            print(f"[extract] 未知状态: {state}, 跳过")
            continue

        strip_path = decoded_dir / f"{state}.png"
        if not strip_path.exists():
            print(f"[extract] 源图片不存在: {strip_path}, 跳过")
            continue

        frame_count = ROW_FRAME_COUNTS[state]
        state_dir = frames_dir / state
        state_dir.mkdir(parents=True, exist_ok=True)

        with Image.open(strip_path) as img:
            strip = img.convert("RGBA")

        for i in range(frame_count):
            left = i * CELL_WIDTH
            right = left + CELL_WIDTH
            frame = strip.crop((left, 0, right, CELL_HEIGHT))
            frame = remove_chroma_background(frame, chroma_key, args.threshold)

            frame_path = state_dir / f"{i:03d}.png"
            frame.save(frame_path, "PNG")
            total_frames += 1

        print(f"[extract] {state}: 提取了 {frame_count} 帧 → {state_dir}")

    print(f"[extract] 完成! 共提取 {total_frames} 帧到 {frames_dir}")


if __name__ == "__main__":
    main()

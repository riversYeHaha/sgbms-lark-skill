#!/usr/bin/env python3
"""Compose a Feishu Pet spritesheet atlas from extracted frames."""

import argparse
from pathlib import Path

from PIL import Image

COLUMNS = 8
ROWS = 9
CELL_WIDTH = 192
CELL_HEIGHT = 208
ATLAS_WIDTH = COLUMNS * CELL_WIDTH
ATLAS_HEIGHT = ROWS * CELL_HEIGHT
IMAGE_SUFFIXES = {".png", ".webp", ".jpg", ".jpeg"}

ROW_SPECS = [
    ("idle", 0, 6),
    ("running-right", 1, 8),
    ("running-left", 2, 8),
    ("waving", 3, 4),
    ("jumping", 4, 5),
    ("failed", 5, 8),
    ("waiting", 6, 6),
    ("running", 7, 6),
    ("review", 8, 6),
]


def image_files(path):
    return sorted(p for p in path.iterdir() if p.suffix.lower() in IMAGE_SUFFIXES)


def paste_centered(atlas, source, row, column):
    frame = source.convert("RGBA")
    if frame.size != (CELL_WIDTH, CELL_HEIGHT):
        frame.thumbnail((CELL_WIDTH, CELL_HEIGHT), Image.Resampling.LANCZOS)
    left = column * CELL_WIDTH + (CELL_WIDTH - frame.width) // 2
    top = row * CELL_HEIGHT + (CELL_HEIGHT - frame.height) // 2
    atlas.alpha_composite(frame, (left, top))


def compose_from_frames(root):
    atlas = Image.new("RGBA", (ATLAS_WIDTH, ATLAS_HEIGHT), (0, 0, 0, 0))
    for state, row, frame_count in ROW_SPECS:
        state_dir = root / state
        if not state_dir.is_dir():
            print(f"[compose] 目录缺失: {state_dir}, 跳过")
            continue

        files = image_files(state_dir)
        if len(files) < frame_count:
            print(f"[compose] {state} 只有 {len(files)} 帧, 需要 {frame_count} 帧")
        for column, frame_path in enumerate(files[:frame_count]):
            with Image.open(frame_path) as frame:
                paste_centered(atlas, frame, row, column)
        print(f"[compose] {state}: {len(files[:frame_count])}/{frame_count} 帧")
    return atlas


def compose_from_source_atlas(path):
    with Image.open(path) as opened:
        source = opened.convert("RGBA")
    if source.size != (ATLAS_WIDTH, ATLAS_HEIGHT):
        raise SystemExit(f"源图集尺寸错误: {source.size}, 期望 ({ATLAS_WIDTH}, {ATLAS_HEIGHT})")

    atlas = Image.new("RGBA", (ATLAS_WIDTH, ATLAS_HEIGHT), (0, 0, 0, 0))
    for state, row, frame_count in ROW_SPECS:
        for column in range(frame_count):
            left = column * CELL_WIDTH
            top = row * CELL_HEIGHT
            cell = source.crop((left, top, left + CELL_WIDTH, top + CELL_HEIGHT))
            atlas.alpha_composite(cell, (left, top))
    return atlas


def save_outputs(atlas, output, webp_output=None):
    output.parent.mkdir(parents=True, exist_ok=True)
    atlas.save(output, "PNG")
    print(f"[compose] PNG: {output}")
    if webp_output:
        webp_output.parent.mkdir(parents=True, exist_ok=True)
        atlas.save(webp_output, format="WEBP", lossless=True, quality=100, method=6)
        print(f"[compose] WebP: {webp_output}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--frames-root", help="帧目录")
    source.add_argument("--source-atlas", help="源图集文件")
    parser.add_argument("--output", required=True, help="输出 PNG 路径")
    parser.add_argument("--webp-output", help="输出 WebP 路径")
    args = parser.parse_args()

    if args.source_atlas:
        atlas = compose_from_source_atlas(Path(args.source_atlas).expanduser().resolve())
    else:
        atlas = compose_from_frames(Path(args.frames_root).expanduser().resolve())

    save_outputs(
        atlas,
        Path(args.output).expanduser().resolve(),
        Path(args.webp_output).expanduser().resolve() if args.webp_output else None,
    )


if __name__ == "__main__":
    main()

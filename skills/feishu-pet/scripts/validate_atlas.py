#!/usr/bin/env python3
"""Validate a Feishu Pet spritesheet atlas."""

import argparse
import json
from pathlib import Path

from PIL import Image

COLUMNS = 8
ROWS = 9
CELL_WIDTH = 192
CELL_HEIGHT = 208
ATLAS_WIDTH = COLUMNS * CELL_WIDTH
ATLAS_HEIGHT = ROWS * CELL_HEIGHT
ROW_BY_INDEX = {
    0: ("idle", 6),
    1: ("running-right", 8),
    2: ("running-left", 8),
    3: ("waving", 4),
    4: ("jumping", 5),
    5: ("failed", 8),
    6: ("waiting", 6),
    7: ("running", 6),
    8: ("review", 6),
}


def alpha_nonzero_count(image):
    alpha = image.getchannel("A")
    return sum(alpha.histogram()[1:])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("atlas", help="图集文件路径")
    parser.add_argument("--json-out", help="JSON 输出路径")
    parser.add_argument("--min-used-pixels", type=int, default=50)
    parser.add_argument("--near-opaque-threshold", type=float, default=0.95)
    parser.add_argument("--allow-opaque", action="store_true")
    args = parser.parse_args()

    atlas_path = Path(args.atlas).expanduser().resolve()
    errors = []
    warnings = []
    cells_data = []

    try:
        with Image.open(atlas_path) as opened:
            source_mode = opened.mode
            source_format = opened.format
            image = opened.convert("RGBA")
    except Exception as exc:
        result = {"ok": False, "errors": [f"无法打开图集: {exc}"], "warnings": []}
        print(json.dumps(result, indent=2))
        raise SystemExit(1)

    if image.size != (ATLAS_WIDTH, ATLAS_HEIGHT):
        errors.append(f"尺寸错误: 期望 {ATLAS_WIDTH}x{ATLAS_HEIGHT}, 实际 {image.width}x{image.height}")

    if source_format not in {"PNG", "WEBP"}:
        errors.append(f"格式错误: 期望 PNG 或 WebP, 实际 {source_format}")

    for row_index in range(ROWS):
        state, frame_count = ROW_BY_INDEX[row_index]
        for column_index in range(COLUMNS):
            left = column_index * CELL_WIDTH
            top = row_index * CELL_HEIGHT
            cell = image.crop((left, top, left + CELL_WIDTH, top + CELL_HEIGHT))
            nontransparent = alpha_nonzero_count(cell)
            used = column_index < frame_count
            cells_data.append({
                "state": state, "row": row_index, "column": column_index,
                "used": used, "nontransparent_pixels": nontransparent,
            })
            if used and nontransparent < args.min_used_pixels:
                errors.append(f"{state} row {row_index} col {column_index} 太稀疏 ({nontransparent}px)")
            if not used and nontransparent != 0:
                errors.append(f"{state} 未使用 col {column_index} 应为透明 ({nontransparent}px)")

    result = {
        "ok": not errors,
        "file": str(atlas_path),
        "format": source_format,
        "mode": source_mode,
        "width": image.width,
        "height": image.height,
        "errors": errors,
        "warnings": warnings,
        "cells": cells_data,
    }

    if args.json_out:
        Path(args.json_out).expanduser().resolve().write_text(
            json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )

    print(json.dumps({k: v for k, v in result.items() if k != "cells"}, indent=2, ensure_ascii=False))
    raise SystemExit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Prepare a Feishu Pet run folder, prompts, and imagegen job manifest."""

import argparse
import json
import math
import os
import re
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw

ATLAS = {"columns": 8, "rows": 9, "cell_width": 192, "cell_height": 208}
ATLAS["width"] = ATLAS["columns"] * ATLAS["cell_width"]
ATLAS["height"] = ATLAS["rows"] * ATLAS["cell_height"]

ROWS = [
    ("idle", 0, 6, "neutral breathing/blinking loop"),
    ("running-right", 1, 8, "rightward locomotion loop"),
    ("running-left", 2, 8, "leftward locomotion loop"),
    ("waving", 3, 4, "greeting gesture"),
    ("jumping", 4, 5, "anticipation, lift, peak, descent, settle"),
    ("failed", 5, 8, "sad or deflated reaction"),
    ("waiting", 6, 6, "patient waiting loop"),
    ("running", 7, 6, "in-place running loop"),
    ("review", 8, 6, "focused inspecting loop"),
]

CHROMA_KEY_CANDIDATES = [
    ("magenta", "#FF00FF"),
    ("cyan", "#00FFFF"),
    ("yellow", "#FFFF00"),
    ("blue", "#0000FF"),
    ("green", "#00FF00"),
]

DEFAULT_PET_NAME = "小 Lark"

DIGITAL_PET_STYLE = (
    "Codex digital pet sprite style: pixel-art-adjacent low-resolution mascot sprite, "
    "compact chibi proportions, chunky whole-body silhouette, thick dark 1-2px outline, "
    "visible stepped/pixel edges, limited palette, flat cel shading with at most one "
    "small highlight and one shadow step, simple readable face, tiny limbs. "
    "Avoid polished illustration, painterly rendering, anime key art, 3D render, "
    "glossy lighting, soft gradients, realistic fur or material texture, "
    "anti-aliased edges, and complex tiny accessories."
)


def slugify(value):
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pet-name", help="宠物名称")
    parser.add_argument("--description", help="宠物描述（一句话）")
    parser.add_argument("--pet-notes", help="详细宠物描述")
    parser.add_argument("--style-notes", help="风格描述")
    parser.add_argument("--reference", action="append", default=[], help="参考图片路径")
    parser.add_argument("--output-dir", help="输出目录")
    parser.add_argument("--force", action="store_true", help="覆盖已有输出")
    parser.add_argument("--chroma-key", default="green", choices=["magenta", "cyan", "yellow", "blue", "green"])
    parser.add_argument("--provider", default="volcengine", help="生图提供商")
    args = parser.parse_args()

    pet_name = args.pet_name or DEFAULT_PET_NAME
    description = args.description or f"{pet_name} 是一个飞书智能宠物，像素精灵风格。"
    pet_slug = slugify(pet_name)
    output_dir = Path(args.output_dir or f"./pet-run-{pet_slug}").resolve()

    if output_dir.exists() and not args.force:
        raise SystemExit(f"输出目录已存在: {output_dir} (使用 --force 覆盖)")

    output_dir.mkdir(parents=True, exist_ok=True)
    prompts_dir = output_dir / "prompts"
    rows_prompts_dir = prompts_dir / "rows"
    rows_prompts_dir.mkdir(parents=True, exist_ok=True)
    refs_dir = output_dir / "references"
    guides_dir = refs_dir / "layout-guides"
    guides_dir.mkdir(parents=True, exist_ok=True)
    decoded_dir = output_dir / "decoded"
    decoded_dir.mkdir(parents=True, exist_ok=True)

    chroma_entry = next((c for c in CHROMA_KEY_CANDIDATES if c[0] == args.chroma_key), CHROMA_KEY_CANDIDATES[4])
    chroma_name, chroma_hex = chroma_entry

    style = args.style_notes or DIGITAL_PET_STYLE
    pet_notes = args.pet_notes or description

    pet_request = {
        "pet_name": pet_name,
        "description": description,
        "pet_notes": pet_notes,
        "style_notes": style,
        "chroma_key": {"name": chroma_name, "hex": chroma_hex},
        "provider": args.provider,
        "atlas": ATLAS,
        "rows": [{"state": r[0], "row_index": r[1], "frame_count": r[2], "description": r[3]} for r in ROWS],
        "references": [str(Path(r).resolve()) for r in args.reference],
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    with open(output_dir / "pet_request.json", "w") as f:
        json.dump(pet_request, f, indent=2, ensure_ascii=False)

    base_prompt = f"""# Base Pet: {pet_name}

Generate a single centered full-body sprite of {pet_name}.

Description: {pet_notes}

Style: {style}

Requirements:
- Centered full-body sprite against a flat uniform chroma-key background ({chroma_name}, {chroma_hex})
- No shadows, gradients, or decorations on the background
- Crisp readability at small size
- The background must be pure flat {chroma_hex} with no variation
"""
    (prompts_dir / "base.md").write_text(base_prompt.strip() + "\n", encoding="utf-8")

    jobs = [
        {
            "id": "base",
            "description": f"base pet pixel sprite for {pet_name}",
            "prompt_file": "prompts/base.md",
            "input_images": [],
            "output_file": "decoded/base.png",
            "status": "pending",
        }
    ]

    for state, row_idx, frame_count, row_desc in ROWS:
        row_prompt = f"""# {state.capitalize()} Row: {pet_name}

Generate a horizontal strip of {frame_count} frames for {pet_name} in {state} animation ({row_desc}).

Style: {style}

Requirements:
- {frame_count} whole-body poses in one continuous horizontal strip
- Frames arranged left-to-right in a single row
- Each frame is a separate centered pose, not a motion-blurred sequence
- Pure flat chroma-key {chroma_name} ({chroma_hex}) background between each slot
- Wide gaps of pure {chroma_hex} separating each slot
- No grid lines, borders, labels, or frame numbers
- No shadows, motion lines, speed lines, or dust effects
- Every frame slot must have a complete unclipped pet pose
- Same exact pet identity, palette, and outline weight as the canonical base
"""
        (rows_prompts_dir / f"{state}.md").write_text(row_prompt.strip() + "\n", encoding="utf-8")

        width = frame_count * ATLAS["cell_width"]
        height = ATLAS["cell_height"]
        guide_img = Image.new("RGB", (width, height), "#FFFFFF")
        draw = ImageDraw.Draw(guide_img)
        for col in range(frame_count):
            left = col * ATLAS["cell_width"]
            right = (col + 1) * ATLAS["cell_width"]
            mid_x = (left + right) // 2
            draw.line([(left, 0), (left, height)], fill="#E0E0E0", width=1)
            draw.line([(right, 0), (right, height)], fill="#E0E0E0", width=1)
            draw.line([(mid_x, height // 4), (mid_x, 3 * height // 4)], fill="#C0C0C0", width=1)
        guide_img.save(guides_dir / f"{state}.png")

        jobs.append({
            "id": state,
            "description": f"{state} row with {frame_count} frames",
            "prompt_file": f"prompts/rows/{state}.md",
            "input_images": ["references/canonical-base.png"],
            "output_file": f"decoded/{state}.png",
            "frame_count": frame_count,
            "row_index": row_idx,
            "status": "pending",
        })

    manifest = {
        "pet_name": pet_name,
        "output_dir": str(output_dir),
        "provider": args.provider,
        "chroma_key": {"name": chroma_name, "hex": chroma_hex},
        "atlas": ATLAS,
        "jobs": jobs,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    with open(output_dir / "imagegen-jobs.json", "w") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(f"[prepare_pet_run] 任务已准备: {output_dir}")
    print(f"  宠物: {pet_name}")
    print(f"  生图提供者: {args.provider}")
    print(f"  色度键: {chroma_name} ({chroma_hex})")
    print(f"  任务: {len(jobs)} (1 个基础 + {len(ROWS)} 个动作行)")
    print(f"  提示词: {prompts_dir}")
    print(f"  接下来: generate_pet_images.py --run-dir {output_dir} --states base")


if __name__ == "__main__":
    main()

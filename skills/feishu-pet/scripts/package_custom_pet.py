#!/usr/bin/env python3
"""Package a Feishu Pet run into the output directory."""

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True, help="运行目录")
    parser.add_argument("--output-dir", help="输出目录")
    args = parser.parse_args()

    run_dir = Path(args.run_dir).resolve()
    output_dir = Path(args.output_dir).expanduser().resolve() if args.output_dir else run_dir / "packaged"

    pet_request = json.loads((run_dir / "pet_request.json").read_text(encoding="utf-8"))
    pet_name = pet_request.get("pet_name", "pet")
    pet_slug = pet_name.lower().replace(" ", "-")

    output_pet_dir = output_dir / pet_slug
    output_pet_dir.mkdir(parents=True, exist_ok=True)

    spritesheet_src = run_dir / "final" / "spritesheet.webp"
    spritesheet_dst = output_pet_dir / "spritesheet.webp"
    if spritesheet_src.exists():
        shutil.copy2(spritesheet_src, spritesheet_dst)

    spritesheet_png_src = run_dir / "final" / "spritesheet.png"
    spritesheet_png_dst = output_pet_dir / "spritesheet.png"
    if spritesheet_png_src.exists():
        shutil.copy2(spritesheet_png_src, spritesheet_png_dst)

    pet_json = {
        "id": pet_slug,
        "displayName": pet_name,
        "description": pet_request.get("description", ""),
        "spritesheetPath": "spritesheet.webp",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    with open(output_pet_dir / "pet.json", "w") as f:
        json.dump(pet_json, f, indent=2, ensure_ascii=False)

    contact_sheet_src = run_dir / "qa" / "contact-sheet.png"
    if contact_sheet_src.exists():
        shutil.copy2(contact_sheet_src, output_pet_dir / "contact-sheet.png")

    print(f"[package] 宠物已打包: {output_pet_dir}")
    print(f"  pet.json: {output_pet_dir / 'pet.json'}")
    print(f"  spritesheet.webp: {output_pet_dir / 'spritesheet.webp'}")
    print(f"  安装到: ~/.codex/pets/{pet_slug}/")


if __name__ == "__main__":
    main()

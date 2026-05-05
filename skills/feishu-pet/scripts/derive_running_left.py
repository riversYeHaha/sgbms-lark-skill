#!/usr/bin/env python3
"""Derive running-left by mirroring running-right when the pet design is symmetric."""

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageOps


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True, help="运行目录")
    parser.add_argument("--confirm-appropriate-mirror", action="store_true", required=True,
                        help="确认镜像对于此宠物设计是合适的")
    parser.add_argument("--decision-note", required=True, help="为什么镜像保留了此宠物的标识")
    args = parser.parse_args()

    run_dir = Path(args.run_dir).resolve()
    source_path = run_dir / "decoded" / "running-right.png"
    if not source_path.is_file():
        raise SystemExit(f"源图片不存在: {source_path}")

    output_path = run_dir / "decoded" / "running-left.png"
    with Image.open(source_path) as img:
        mirrored = ImageOps.mirror(img.convert("RGBA"))
    mirrored.save(output_path, "PNG")

    manifest_path = run_dir / "imagegen-jobs.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    job = next((j for j in manifest.get("jobs", []) if j["id"] == "running-left"), None)
    if job:
        job["status"] = "complete"
        job["derived_from"] = "running-right"
        job["mirror_decision"] = {"approved": True, "note": args.decision_note}
        job["recorded_at"] = datetime.now(timezone.utc).isoformat()
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"[derive] running-left 已从 running-right 镜像生成: {output_path}")
    print(f"[derive] 决策: {args.decision_note}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Record a generated image result into the run manifest."""

import argparse
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path


def file_sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True, help="运行目录")
    parser.add_argument("--job-id", required=True, help="任务 ID（'base' 或状态名如 'idle'）")
    parser.add_argument("--source", required=True, help="生成的源图片路径")
    args = parser.parse_args()

    run_dir = Path(args.run_dir).resolve()
    manifest_path = run_dir / "imagegen-jobs.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    source = Path(args.source).resolve()
    if not source.is_file():
        raise SystemExit(f"源图片不存在: {source}")

    job = None
    for j in manifest.get("jobs", []):
        if j["id"] == args.job_id:
            job = j
            break

    if not job:
        raise SystemExit(f"找不到任务: {args.job_id}")

    output_rel = job.get("output_file", f"decoded/{args.job_id}.png")
    output_path = run_dir / output_rel
    output_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, output_path)
    sha = file_sha256(output_path)

    job["status"] = "complete"
    job["source_sha256"] = sha
    job["output_sha256"] = sha
    job["recorded_at"] = datetime.now(timezone.utc).isoformat()
    job["source_file"] = str(source)

    if args.job_id == "base":
        canonical = run_dir / "references" / "canonical-base.png"
        canonical.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, canonical)
        print(f"[record] 标准基础形象已复制: {canonical}")

    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"[record] 任务 {args.job_id} 已记录 (SHA256: {sha[:16]}...)")


if __name__ == "__main__":
    main()

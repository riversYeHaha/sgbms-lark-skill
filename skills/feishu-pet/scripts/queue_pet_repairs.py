#!/usr/bin/env python3
"""Queue repair jobs for failed Feishu Pet rows."""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True, help="运行目录")
    parser.add_argument("--review-json", help="review.json 路径")
    args = parser.parse_args()

    run_dir = Path(args.run_dir).resolve()
    review_path = Path(args.review_json).expanduser().resolve() if args.review_json else run_dir / "qa" / "review.json"

    if not review_path.exists():
        review_path = run_dir / "final" / "validation.json"

    if not review_path.exists():
        raise SystemExit(f"review/validation JSON 不存在: {review_path}")

    review = json.loads(review_path.read_text(encoding="utf-8"))

    errors = []
    if isinstance(review, dict):
        if review.get("errors"):
            errors = review["errors"]
        if review.get("cells"):
            for cell in review["cells"]:
                pass

    manifest_path = run_dir / "imagegen-jobs.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    failed_states = set()
    if errors:
        print(f"[repair] 发现 {len(errors)} 个错误:")
        for err in errors:
            print(f"  - {err}")
            for state in ["idle", "running-right", "running-left", "waving", "jumping", "failed", "waiting", "running", "review"]:
                if state in str(err).lower():
                    failed_states.add(state)

    if not failed_states:
        print("[repair] 未找到需要修复的行")
        return

    for state in failed_states:
        job = next((j for j in manifest.get("jobs", []) if j["id"] == state), None)
        if job:
            job["status"] = "pending"
            job["repair_reason"] = "; ".join(errors)
            job["repair_attempt"] = job.get("repair_attempt", 0) + 1
            print(f"[repair] {state} 需要修复: {job['repair_reason']}")

    manifest["updated_at"] = datetime.now(timezone.utc).isoformat()
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"[repair] 修复队列已更新。运行 generate_pet_images.py 重新生成失败的行。")


if __name__ == "__main__":
    main()

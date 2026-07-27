"""File Helper Skill — 执行入口"""
import os
from pathlib import Path


def run(args: dict):
    """
    args: {
        "action": "du_large | rename_pattern | count_files",
        "path": "目标目录",
        ...
    }
    """
    action = args.get("action", "")
    path = Path(args.get("path", ".")).expanduser().resolve()

    if action == "du_large":
        files = []
        for root, _, fnames in os.walk(path):
            for f in fnames:
                fp = Path(root) / f
                try:
                    files.append((fp, fp.stat().st_size))
                except OSError:
                    continue
        files.sort(key=lambda x: x[1], reverse=True)
        top = files[:20]
        lines = [f"{size:>12,} bytes  {p.relative_to(path)}" for p, size in top]
        return {"output": "\n".join(lines)}

    elif action == "count_files":
        counts = {}
        for root, _, fnames in os.walk(path):
            for f in fnames:
                ext = Path(f).suffix or "(no ext)"
                counts[ext] = counts.get(ext, 0) + 1
        sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        lines = [f"{cnt:>6}  {ext}" for ext, cnt in sorted_counts[:15]]
        return {"output": "\n".join(lines)}

    return {"error": f"未知 action: {action}"}

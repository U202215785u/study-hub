"""批量导入工具 — Second Self 数据大规模入库

支持来源：
  1. Markdown 文件夹（每个 .md → 一条记忆）
  2. JSON 文件（数组格式，每条必须含 content）
  3. TXT 文件（按分隔符切分，如 --- 或 空行）
  4. CSV 文件（列：content, title, domain, significance...）
  5. 聊天记录 TXT（复用 pipeline_chat_manual 逻辑）

用法：
  python batch_import.py md   ./my-notes/  --domain "设计" --field knowledge
  python batch_import.py json ./data.json  --domain "学习"
  python batch_import.py txt  ./articles.txt --split "---" --domain "文章"
  python batch_import.py csv  ./data.csv   --domain "工作"

"""
import argparse
import base64
import csv
import json
import sys
from pathlib import Path

from gateway_paths import ROOT
from memory_store import insert_entry


def import_md_folder(folder: str, domain: str = "general", field: str = "knowledge",
                     significance: str = "B", dry_run: bool = False) -> dict:
    """批量导入 Markdown 文件夹。"""
    path = Path(folder)
    if not path.is_dir():
        return {"error": f"不是文件夹: {folder}"}

    files = sorted(path.rglob("*.md"))
    imported = []
    for f in files:
        content = f.read_text(encoding="utf-8")
        title = f.stem
        if dry_run:
            imported.append({"title": title, "path": str(f), "action": "dry_run"})
            continue
        entry_id = insert_entry(
            source="batch_import_md",
            type="capture",
            content=content,
            context={"domain": domain, "title": title, "path": str(f)},
            significance=significance,
            field=field,
        )
        imported.append({"entry_id": entry_id, "title": title})
    return {"ok": True, "count": len(imported), "items": imported}


def import_json_file(filepath: str, domain: str = "general", field: str = "knowledge",
                     significance: str = "B", dry_run: bool = False) -> dict:
    """批量导入 JSON 文件。"""
    path = Path(filepath)
    if not path.exists():
        return {"error": f"文件不存在: {filepath}"}

    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list):
        return {"error": "JSON 根必须是数组或对象"}

    imported = []
    for item in data:
        if not isinstance(item, dict):
            continue
        content = item.get("content") or item.get("text") or item.get("body")
        if not content:
            continue
        title = item.get("title", item.get("name", "未命名"))
        item_domain = item.get("domain", domain)
        item_field = item.get("field", field)
        item_sig = item.get("significance", significance)
        if dry_run:
            imported.append({"title": title, "action": "dry_run"})
            continue
        entry_id = insert_entry(
            source="batch_import_json",
            type=item.get("type", "capture"),
            content=str(content),
            context={"domain": item_domain, "title": title, **{k: v for k, v in item.items()
                     if k not in ("content", "text", "body", "title", "type", "significance", "field", "domain")}},
            significance=item_sig,
            field=item_field,
        )
        imported.append({"entry_id": entry_id, "title": title})
    return {"ok": True, "count": len(imported), "items": imported}


def import_txt_file(filepath: str, split: str = "\n---\n", domain: str = "general",
                    field: str = "knowledge", significance: str = "B", dry_run: bool = False) -> dict:
    """批量导入 TXT 文件，按分隔符切分。"""
    path = Path(filepath)
    if not path.exists():
        return {"error": f"文件不存在: {filepath}"}

    text = path.read_text(encoding="utf-8")
    parts = text.split(split)
    imported = []
    for i, part in enumerate(parts):
        part = part.strip()
        if not part or len(part) < 10:
            continue
        title = part.split("\n")[0][:50] if part.startswith("#") else f"段落-{i+1}"
        if dry_run:
            imported.append({"title": title, "action": "dry_run"})
            continue
        entry_id = insert_entry(
            source="batch_import_txt",
            type="capture",
            content=part,
            context={"domain": domain, "title": title, "part_index": i + 1},
            significance=significance,
            field=field,
        )
        imported.append({"entry_id": entry_id, "title": title})
    return {"ok": True, "count": len(imported), "items": imported}


def import_csv_file(filepath: str, dry_run: bool = False) -> dict:
    """批量导入 CSV 文件。
    期望列（至少含 content）：content, title, domain, field, significance, type
    """
    path = Path(filepath)
    if not path.exists():
        return {"error": f"文件不存在: {filepath}"}

    imported = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            content = row.get("content", "").strip()
            if not content:
                continue
            title = row.get("title", f"csv-{i+1}")
            domain = row.get("domain", "general")
            field = row.get("field", "knowledge")
            significance = row.get("significance", "B")
            entry_type = row.get("type", "capture")
            if dry_run:
                imported.append({"title": title, "action": "dry_run"})
                continue
            entry_id = insert_entry(
                source="batch_import_csv",
                type=entry_type,
                content=content,
                context={"domain": domain, "title": title},
                significance=significance,
                field=field,
            )
            imported.append({"entry_id": entry_id, "title": title})
    return {"ok": True, "count": len(imported), "items": imported}


def main():
    parser = argparse.ArgumentParser(description="Second Self 批量导入工具")
    parser.add_argument("format", choices=["md", "json", "txt", "csv"], help="数据源格式")
    parser.add_argument("source", help="源文件或文件夹路径")
    parser.add_argument("--domain", default="general", help="记忆域（默认 general）")
    parser.add_argument("--field", default="knowledge", help="记忆场（默认 knowledge）")
    parser.add_argument("--significance", default="B", choices=["A", "B", "C"], help="重要性等级")
    parser.add_argument("--split", default="\n---\n", help="TXT 分隔符（默认 \\n---\\n）")
    parser.add_argument("--dry-run", action="store_true", help="试运行，不写入数据库")

    args = parser.parse_args()

    if args.format == "md":
        result = import_md_folder(args.source, args.domain, args.field, args.significance, args.dry_run)
    elif args.format == "json":
        result = import_json_file(args.source, args.domain, args.field, args.significance, args.dry_run)
    elif args.format == "txt":
        result = import_txt_file(args.source, args.split, args.domain, args.field, args.significance, args.dry_run)
    elif args.format == "csv":
        result = import_csv_file(args.source, args.dry_run)
    else:
        result = {"error": "未知格式"}

    print(json.dumps(result, ensure_ascii=False, indent=2))
    if "error" in result:
        sys.exit(1)


if __name__ == "__main__":
    main()

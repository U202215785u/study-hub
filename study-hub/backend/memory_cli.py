#!/usr/bin/env python3
"""
Study-Hub Memory CLI
不支持 MCP 的工具（Cursor、终端 Kimi 等）可以通过此 CLI 操作记忆系统。

用法：
    python memory_cli.py add "喜欢辣的食物" --cat preferences
    python memory_cli.py recall "吃什么"
    python memory_cli.py extract conversation.txt
    python memory_cli.py list --cat preferences
    python memory_cli.py delete 42
"""

import argparse
import json
import os
import sys
import httpx

API_BASE = os.getenv("STUDY_HUB_API_BASE", "http://localhost:8741").rstrip("/")


def api_post(path: str, body: dict) -> dict:
    r = httpx.post(f"{API_BASE}{path}", json=body, timeout=30)
    r.raise_for_status()
    return r.json()


def api_get(path: str) -> dict:
    r = httpx.get(f"{API_BASE}{path}", timeout=30)
    r.raise_for_status()
    return r.json()


def cmd_add(args):
    body = {
        "content": args.content,
        "category": args.cat or "other",
        "tags": args.tags or [],
        "source_tool": args.source or "cli",
        "importance": args.importance or 3,
    }
    data = api_post("/memory/remember", body)
    if "error" in data:
        print(f"❌ 失败: {data['error']}")
        sys.exit(1)
    print(f"✅ 已记住 (ID {data['id']}): {data['content']}")


def cmd_recall(args):
    data = api_get(f"/memory/recall?q={args.query}&top_k={args.top_k or 5}")
    results = data.get("results", [])
    if not results:
        print(f"未找到与「{args.query}」相关的记忆。")
        return
    print(f"关于「{args.query}」的记忆：")
    for r in results:
        tags = ", ".join(r.get("tags", []))
        tag_str = f" [{tags}]" if tags else ""
        print(f"  (ID {r['id']}) {r['content']}{tag_str}")


def cmd_extract(args):
    path = args.file
    if not os.path.isfile(path):
        print(f"❌ 文件不存在: {path}")
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    body = {"text": text, "source_tool": args.source or "cli"}
    data = api_post("/memory/extract", body)
    added = data.get("added", 0)
    skipped = data.get("skipped", 0)
    print(f"提取完成：新增 {added} 条，跳过重复 {skipped} 条。")
    for item in data.get("items", []):
        print(f"  + {item['content']}")
    for sc in data.get("skipped_contents", []):
        print(f"  - (重复) {sc}")


def cmd_list(args):
    cat = args.cat or ""
    data = api_get(f"/memory/list?cat={cat}&limit={args.limit or 50}")
    items = data.get("items", [])
    total = data.get("total", 0)
    if not items:
        print("记忆库为空。")
        return
    print(f"共 {total} 条记忆：")
    for r in items:
        tags = ", ".join(r.get("tags", []))
        tag_str = f" [{tags}]" if tags else ""
        status = r.get("status", "active")
        status_icon = "✅" if status == "active" else "❌"
        print(f"  {status_icon} (ID {r['id']}) [{r.get('category','other')}] {r['content']}{tag_str}")


def cmd_delete(args):
    r = httpx.delete(f"{API_BASE}/memory/{args.id}", timeout=30)
    r.raise_for_status()
    data = r.json()
    if data.get("deleted"):
        print(f"✅ 已删除记忆 #{args.id}")
    else:
        print(f"❌ 删除失败: {data.get('error', '未知错误')}")


def main():
    parser = argparse.ArgumentParser(description="Study-Hub Memory CLI")
    sub = parser.add_subparsers(dest="command")

    p_add = sub.add_parser("add", help="添加一条记忆")
    p_add.add_argument("content", help="记忆内容")
    p_add.add_argument("--cat", help="分类")
    p_add.add_argument("--tags", nargs="+", help="标签")
    p_add.add_argument("--source", help="来源工具")
    p_add.add_argument("--importance", type=int, help="重要性 1-5")

    p_recall = sub.add_parser("recall", help="语义搜索记忆")
    p_recall.add_argument("query", help="搜索关键词")
    p_recall.add_argument("--top_k", type=int, default=5, help="返回数量")

    p_extract = sub.add_parser("extract", help="从文本文件中提取事实")
    p_extract.add_argument("file", help="文本文件路径")
    p_extract.add_argument("--source", help="来源工具")

    p_list = sub.add_parser("list", help="列出记忆")
    p_list.add_argument("--cat", help="按分类筛选")
    p_list.add_argument("--limit", type=int, default=50, help="返回数量")

    p_delete = sub.add_parser("delete", help="删除记忆")
    p_delete.add_argument("id", type=int, help="记忆 ID")

    args = parser.parse_args()
    if args.command == "add":
        cmd_add(args)
    elif args.command == "recall":
        cmd_recall(args)
    elif args.command == "extract":
        cmd_extract(args)
    elif args.command == "list":
        cmd_list(args)
    elif args.command == "delete":
        cmd_delete(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

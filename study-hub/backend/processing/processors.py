"""
文件处理器映射 — 统一入口，watcher 和 upload 共用。
加新格式只需在这里注册，不碰其他文件。
"""
import os, hashlib

EXT_HANDLERS = {}

def register(*extensions):
    """装饰器：把函数注册为指定扩展名的处理器"""
    def decorator(fn):
        for ext in extensions:
            EXT_HANDLERS[ext] = fn
        return fn
    return decorator

def can_handle(ext: str) -> bool:
    return ext in EXT_HANDLERS

def process_bytes(data: bytes, ext: str) -> str:
    """二进制入口（PDF 等），按扩展名分发"""
    handler = EXT_HANDLERS.get(ext)
    if not handler:
        raise ValueError(f"不支持的文件格式: {ext}")
    return handler(data)

def process_path(filepath: str) -> tuple[str, str, str]:
    """文件路径入口（watcher），返回 (text, ext, content_hash)。处理完的文件由调用方归档。"""
    ext = os.path.splitext(filepath)[1].lower()
    if ext not in EXT_HANDLERS:
        raise ValueError(f"不支持的文件格式: {ext}")
    with open(filepath, 'rb') as f:
        data = f.read()
    text = EXT_HANDLERS[ext](data)
    content_hash = sha256(text)
    return text, ext, content_hash

def sha256(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8', errors='replace')).hexdigest()

def is_duplicate(content_hash: str) -> bool:
    """检查内容哈希是否已存在于数据库"""
    from database import get_db
    conn = get_db()
    row = conn.execute("SELECT id FROM documents WHERE content_hash = ? LIMIT 1", (content_hash,)).fetchone()
    conn.close()
    return row is not None

# ── 处理器注册 ──────────────────────────────────────────

@register('.txt', '.md', '.html', '.json', '.py', '.js', '.ts', '.css',
         '.xml', '.yml', '.yaml', '.toml', '.ini', '.cfg', '.conf',
         '.csv', '.log', '.sh', '.bat', '.ps1', '.sql', '.tex', '.rst')
def _plain_text(data: bytes) -> str:
    return data.decode('utf-8', errors='replace')

@register('.pdf')
def _pdf(data: bytes) -> str:
    try:
        import fitz
        doc = fitz.open(stream=data, filetype='pdf')
        text = ''
        for page in doc:
            text += page.get_text() + '\n'
        doc.close()
        return text
    except ImportError:
        return '[PDF 解析需要安装 PyMuPDF: pip install PyMuPDF]'
    except Exception as e:
        return f'[PDF 解析失败: {e}]'

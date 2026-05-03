import re

CHUNK_SIZE = 500

def chunk_text(text: str, chunk_size: int = CHUNK_SIZE) -> list[str]:
    """
    将文本按句子边界分块，每块约 chunk_size 字符。
    在句号、换行等自然断点处切开，不截断句子。
    """
    if not text or not text.strip():
        return []

    # 按句子分割（。！？!?\n 等）
    sentences = re.split(r'(?<=[。！？!?\n])\s*', text)
    sentences = [s.strip() for s in sentences if s.strip()]

    chunks = []
    current = ""
    for s in sentences:
        if len(current) + len(s) <= chunk_size:
            current += s
        else:
            if current:
                chunks.append(current.strip())
            # 如果单句超过 chunk_size，硬切
            if len(s) > chunk_size:
                for i in range(0, len(s), chunk_size):
                    chunks.append(s[i:i+chunk_size].strip())
                current = ""
            else:
                current = s

    if current.strip():
        chunks.append(current.strip())

    return chunks

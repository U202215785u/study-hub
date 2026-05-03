FROM python:3.12-slim

WORKDIR /app

# 系统依赖：PyMuPDF + sentence-transformers 编译
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ libgl1-mesa-glx libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# HF 镜像（国内网络加速）
ENV HF_ENDPOINT=https://hf-mirror.com

# 先用 CPU 版 PyTorch，避免拉 CUDA 版本导致镜像膨胀
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY requirements-mcp.txt .
RUN pip install --no-cache-dir -r requirements-mcp.txt

# 预下载中文 embedding 模型（首次启动零等待）
# 轻量 bge-small-zh-v1.5 (~95MB)；追求效果可改为 bge-base-zh 或 bge-large-zh
ARG EMBED_MODEL=BAAI/bge-small-zh-v1.5
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('${EMBED_MODEL}')"

COPY backend/ .
COPY frontend/ /frontend
COPY mcp_server.py .

EXPOSE 8741

CMD ["python", "main.py"]

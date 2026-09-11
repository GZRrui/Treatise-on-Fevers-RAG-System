FROM python:3.11.15-slim-bookworm

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .
RUN pip install --no-cache-dir --require-hashes -r requirements.txt

# 复制应用代码
COPY . .

# 创建存储目录
RUN mkdir -p storage/vector_store storage/logs

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]

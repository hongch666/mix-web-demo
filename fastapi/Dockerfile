# 使用官方Python运行时作为基础镜像
FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY . /app/

# 安装Python依赖
RUN pip install --upgrade pip setuptools && \
    pip install -e .

# 创建日志目录和文件目录
RUN mkdir -p /app/logs/fastapi \
    && mkdir -p /app/static/pic \
    && mkdir -p /app/static/excel \
    && mkdir -p /app/static/upload

# 暴露端口（默认8084）
EXPOSE 8084

# 启动命令
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8084"]

# 使用官方Python运行时作为基础镜像
FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple \
    PIP_TRUSTED_HOST=mirrors.aliyun.com

# 先复制依赖清单，单独安装依赖，方便缓存复用
COPY requirements.txt /app/

# 安装Python依赖
RUN pip install --upgrade pip setuptools && \
    pip install -r requirements.txt

# 再复制项目代码，避免代码改动触发依赖重装
COPY . /app/

# 创建日志目录和文件目录
RUN mkdir -p /app/logs/fastapi \
    && mkdir -p /app/static/pic \
    && mkdir -p /app/static/excel

# 暴露端口（默认8084）
EXPOSE 8084

# 启动命令
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8084"]

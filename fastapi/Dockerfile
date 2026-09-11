# 使用官方Python运行时作为基础镜像
FROM python:3.12-slim-bookworm

# 构建时接收代理，供 RUN 里的 apt / pip 使用
ARG http_proxy
ARG https_proxy
ARG HTTP_PROXY
ARG HTTPS_PROXY

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple \
    PIP_TRUSTED_HOST=mirrors.aliyun.com

# 词云需使用中文字体
# 源改为 HTTPS（走代理稳定），保留代理环境变量
RUN set -eux; \
    if [ -f /etc/apt/sources.list.d/debian.sources ]; then \
    sed -i 's|deb.debian.org|mirrors.aliyun.com|g; s|http://|https://|g' /etc/apt/sources.list.d/debian.sources; \
    fi; \
    if [ -f /etc/apt/sources.list ]; then \
    sed -i 's|deb.debian.org|mirrors.aliyun.com|g; s|http://|https://|g' /etc/apt/sources.list; \
    fi; \
    apt-get -o Acquire::Retries=5 update; \
    apt-get -o Acquire::Retries=5 \
    -o Acquire::http::Timeout=30 \
    -o Acquire::https::Timeout=30 \
    install -y --no-install-recommends fonts-noto-cjk; \
    rm -rf /var/lib/apt/lists/*

# 先复制依赖清单，单独安装依赖，方便缓存复用
COPY requirements.txt /app/

# 安装Python依赖
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip setuptools && \
    pip install -r requirements.txt

# 再复制项目代码，避免代码改动触发依赖重装
COPY . /app/

# 创建日志目录和文件目录
RUN mkdir -p /app/logs/fastapi \
    && mkdir -p /app/static/pic \
    && mkdir -p /app/static/excel

# 暴露端口（默认8084）
EXPOSE 8084

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import sys, urllib.request; sys.exit(0 if urllib.request.urlopen('http://localhost:8084/test/fastapi', timeout=5).getcode() == 200 else 1)" || exit 1

# 启动命令
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8084"]

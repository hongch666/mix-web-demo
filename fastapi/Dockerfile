# 构建阶段：安装运行期依赖，并把业务源码编译为字节码后删除 .py
# 运行阶段只复制字节码与依赖，镜像内不存在可直接阅读的业务源码
FROM python:3.12-slim-bookworm AS builder

# 构建时接收代理，供 RUN 里的 pip 使用
ARG http_proxy
ARG https_proxy
ARG HTTP_PROXY
ARG HTTPS_PROXY

WORKDIR /app

# 依赖装在独立虚拟环境里，便于整体复制到运行阶段，避免把构建缓存与工具链带进正式镜像
ENV PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple \
    PIP_TRUSTED_HOST=mirrors.aliyun.com

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 先复制依赖清单，单独安装依赖，方便缓存复用
COPY requirements.txt /app/
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip setuptools && \
    pip install -r requirements.txt

# 再复制项目代码，避免代码改动触发依赖重装
COPY . /app/

# -b 让 .pyc 与源码同目录（main.pyc、__init__.pyc），删除 .py 后仍可按模块导入
# -f 强制重新编译，避免命中华而不实的旧编译产物
RUN set -eux; \
    python -m compileall -b -f -q main.py app; \
    find /app -name '*.py' -delete; \
    find /app -type d -name '__pycache__' -prune -exec rm -rf {} +; \
    rm -f /app/requirements.txt /app/pyproject.toml /app/uv.lock

# 运行阶段：仅保留解释器、运行期依赖与字节码
FROM python:3.12-slim-bookworm

# 构建时接收代理，供 RUN 里的 apt 使用
ARG http_proxy
ARG https_proxy
ARG HTTP_PROXY
ARG HTTPS_PROXY

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    TZ=Asia/Shanghai

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
    install -y --no-install-recommends fonts-noto-cjk tzdata; \
    rm -rf /var/lib/apt/lists/*

# 依赖与编译产物来自构建阶段，业务代码只有 .pyc
COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /app /app

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

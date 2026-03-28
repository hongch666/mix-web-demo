#!/bin/bash

set -e

WORKDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="$WORKDIR/docker-compose.yml"

# 查找可用的 compose 命令
if command -v docker-compose >/dev/null 2>&1; then
    COMPOSE_CMD="docker-compose"
elif command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
else
    echo "Error: docker-compose 或 Docker Compose CLI 未安装"
    exit 1
fi

cd "$WORKDIR"

echo "停止并删除 docker-compose 服务..."

$COMPOSE_CMD -f "$COMPOSE_FILE" down -v

echo "服务已停止并清理卷。"

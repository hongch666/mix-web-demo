#!/bin/bash

set -e

WORKDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="$WORKDIR/docker-compose.yml"

if ! command -v docker-compose >/dev/null 2>&1 && ! command -v docker >/dev/null 2>&1; then
    echo "Error: docker-compose 或 Docker 未安装"
    exit 1
fi

cd "$WORKDIR"

echo "停止并删除 docker-compose 服务..."

docker-compose -f "$COMPOSE_FILE" down -v

echo "服务已停止并清理卷。"

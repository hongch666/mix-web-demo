#!/bin/bash

# 清理网关容器 mix-gateway
# dev 模式使用 gateway/docker-compose.yml（项目名 gateway），根 compose 使用
# docker-compose.yml（项目名 mix-web-demo），两者的网关服务都硬编码了
# container_name: mix-gateway，由于不属于同一个 compose 项目，任何一方残留
# 都会导致另一方启动时报 "container name already in use"
# 在启动网关前、或 dev 停止后调用本脚本即可避免该冲突

WORKDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GATEWAY_CONTAINER="mix-gateway"
GATEWAY_COMPOSE="$WORKDIR/gateway/docker-compose.yml"

if ! command -v docker >/dev/null 2>&1; then
    exit 0
fi

# 1. 删除占用 mix-gateway 名称的容器，运行中与已退出的都会被清理
if docker ps -a --format '{{.Names}}' 2>/dev/null | grep -qx "$GATEWAY_CONTAINER"; then
    echo "清理网关容器 $GATEWAY_CONTAINER ..."
    docker rm -f "$GATEWAY_CONTAINER" >/dev/null 2>&1 || \
        echo "警告：网关容器 $GATEWAY_CONTAINER 删除失败，可手动执行 docker rm -f $GATEWAY_CONTAINER"
fi

# 2. 清理 dev 模式网关项目残留的一次性容器（如 gateway-log-init）
if [ -f "$GATEWAY_COMPOSE" ]; then
    COMPOSE_CMD=""
    if command -v docker-compose >/dev/null 2>&1; then
        COMPOSE_CMD="docker-compose"
    elif docker compose version >/dev/null 2>&1; then
        COMPOSE_CMD="docker compose"
    fi

    if [ -n "$COMPOSE_CMD" ]; then
        $COMPOSE_CMD -f "$GATEWAY_COMPOSE" -p gateway down --remove-orphans >/dev/null 2>&1 || true
    fi
fi

exit 0

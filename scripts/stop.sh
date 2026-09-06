#!/bin/bash

tmux kill-session -t multi-services 2>/dev/null || true

SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# dev 模式的网关容器与根 compose 的 mix-gateway 同名，仅 stop 不移除会在
# 下次启动（compose up 或 dev seq）时报容器名冲突，这里直接清除
if command -v docker >/dev/null 2>&1; then
    bash "$SCRIPTS_DIR/gateway-cleanup.sh"
fi

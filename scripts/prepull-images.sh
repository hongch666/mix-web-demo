#!/bin/bash

# 脚本说明：
# 逐个预拉取 compose 引用的镜像，规避 docker compose v2.35.x 的并发拉取崩溃
#   现象：docker compose up 时 fatal error: concurrent map writes
#         （栈顶在 pkg/compose.(*composeService).pullRequiredImages）
#   原因：compose 用 errgroup 并发拉取镜像时对同一个 map 写入，属其自身 bug
#         github.com/docker/compose#12747，v2.36.0 起修复
#   兜底：先用 docker CLI 串行拉一遍，镜像命中本地缓存后 compose up 不再进入并发拉取分支
#   彻底修复：把 docker compose 升到 >= v2.36.0（或临时降到 <= v2.27.x）
# 用法：./scripts/prepull-images.sh <compose 文件> [compose 命令，默认 "docker compose"]
# 说明：只拉本地缺失的镜像；compose config --images 不支持的旧版 compose 直接跳过

set -u

COMPOSE_FILE="${1:-}"
COMPOSE_CMD="${2:-docker compose}"

if [ -z "$COMPOSE_FILE" ] || [ ! -f "$COMPOSE_FILE" ]; then
    exit 0
fi

# config --images 只解析编排文件，不触发任何拉取；docker-compose v1 不支持该参数，取不到就跳过
images="$($COMPOSE_CMD -f "$COMPOSE_FILE" config --images 2>/dev/null | sort -u)"
if [ -z "$images" ]; then
    exit 0
fi

while IFS= read -r image; do
    [ -z "$image" ] && continue
    # 本地已有则跳过，避免无谓的网络请求
    if docker image inspect "$image" >/dev/null 2>&1; then
        continue
    fi
    echo "预拉取镜像: $image"
    if ! docker pull "$image"; then
        # 拉取失败不阻断启动，交给 compose 自己处理（可能配置了镜像代理或私有仓库）
        echo "警告：镜像预拉取失败，交由 compose 处理: $image"
    fi
done <<< "$images"

exit 0

#!/bin/bash

# 脚本说明：
# 这个脚本用于生成 GoZero API 代码

WORKDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$WORKDIR"

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查 goctl 工具是否安装
if ! command -v goctl &> /dev/null; then
    log_error "goctl 工具未安装"
    log_info "请先运行: go install github.com/zeromicro/go-zero/tools/goctl@latest"
    exit 1
fi

log_info "开始生成 GoZero API 代码..."

# 调用 genApi.sh
if bash "$WORKDIR/gozero/script/goctl/genApi.sh" "$@"; then
    log_info "GoZero API 代码生成成功"
else
    log_error "GoZero API 代码生成失败"
    exit 1
fi

log_info "API 代码生成完成"

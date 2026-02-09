#!/bin/bash

# 脚本说明：
# 这个脚本用于初始化 Swagger 文档

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

# 检查 swag 工具是否安装
if ! command -v swag &> /dev/null; then
    log_error "swag 工具未安装"
    log_info "请先运行: go install github.com/swaggo/swag/cmd/swag@latest"
    exit 1
fi

log_info "开始初始化 Swagger 文档..."

# Gin 项目 Swagger 初始化
log_info "初始化 Gin 项目的 Swagger 文档..."
cd "$WORKDIR/gin"
if swag init -g api/router.go; then
    log_info "Gin Swagger 文档初始化成功"
else
    log_error "Gin Swagger 文档初始化失败"
    exit 1
fi

log_info "Swagger 文档初始化完成"

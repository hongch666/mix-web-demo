#!/bin/bash

# 脚本说明：
# 检查静态 OpenAPI 产物声明的错误码与源码实际使用的错误码是否一致
# 扫描四个服务的状态码常量与字面量，报告「源码出现但文档未声明」的码，用于发现遗漏的接口级错误响应
# 用法：./scripts/check-error-codes.sh [service...] [--strict]
#   service 可选值：spring、gozero、nestjs、fastapi，不指定时检查全部服务
#   --strict 存在差异时返回非零退出码（默认只报告）

WORKDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

check_error_codes() {
    print_info "检查 OpenAPI 错误码与源码的一致性..."
    if command -v python >/dev/null 2>&1; then
        python "$WORKDIR/scripts/check-error-codes.py" "$@"
        return
    fi
    if command -v python3 >/dev/null 2>&1; then
        python3 "$WORKDIR/scripts/check-error-codes.py" "$@"
        return
    fi
    print_warn "未检测到 python，跳过错误码一致性检查"
    return 2
}

check_error_codes "$@"

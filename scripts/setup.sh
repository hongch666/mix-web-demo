#!/bin/bash

#!/bin/bash

# 多语言技术栈系统 - 依赖安装配置脚本
# 适用于 Linux 系统

# 加载环境变量
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# 获取脚本所在目录的父目录（项目根目录）
WORKDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$WORKDIR"

set -e  # 遇到错误立即退出

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检测操作系统
detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$ID
    else
        log_error "无法检测操作系统"
        exit 1
    fi
}

# 检查命令是否存在
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 检查并安装系统依赖
check_and_install_system_deps() {
    log_info "检查系统依赖..."
    
    local packages_to_install=()
    
    # 检查 libpq-dev (PostgreSQL 开发库)
    if ! dpkg -l | grep -q libpq-dev 2>/dev/null && ! rpm -q postgresql-devel 2>/dev/null; then
        case "$OS" in
            ubuntu|debian)
                packages_to_install+=("libpq-dev")
                ;;
            centos|rhel|fedora)
                packages_to_install+=("postgresql-devel")
                ;;
            arch)
                packages_to_install+=("postgresql-libs")
                ;;
        esac
    fi
    
    # 检查 python3-dev
    if ! dpkg -l | grep -q python3-dev 2>/dev/null && ! rpm -q python3-devel 2>/dev/null; then
        case "$OS" in
            ubuntu|debian)
                packages_to_install+=("python3-dev")
                ;;
            centos|rhel|fedora)
                packages_to_install+=("python3-devel")
                ;;
            arch)
                packages_to_install+=("python")
                ;;
        esac
    fi
    
    # 检查 gcc
    if ! command_exists gcc; then
        case "$OS" in
            ubuntu|debian)
                packages_to_install+=("build-essential")
                ;;
            centos|rhel|fedora)
                packages_to_install+=("gcc" "gcc-c++" "make")
                ;;
            arch)
                packages_to_install+=("base-devel")
                ;;
        esac
    fi
    
    if [ ${#packages_to_install[@]} -ne 0 ]; then
        log_warn "需要安装以下系统依赖: ${packages_to_install[*]}"
        echo "是否现在安装? (需要 sudo 权限) [y/N]"
        read -p "请输入: " install_deps
        
        if [[ "$install_deps" =~ ^[Yy]$ ]]; then
            case "$OS" in
                ubuntu|debian)
                    sudo apt-get update
                    sudo apt-get install -y "${packages_to_install[@]}"
                    ;;
                centos|rhel)
                    sudo yum install -y "${packages_to_install[@]}"
                    ;;
                fedora)
                    sudo dnf install -y "${packages_to_install[@]}"
                    ;;
                arch)
                    sudo pacman -S --noconfirm "${packages_to_install[@]}"
                    ;;
                *)
                    log_error "不支持的操作系统: $OS"
                    log_error "请手动安装以下依赖: ${packages_to_install[*]}"
                    exit 1
                    ;;
            esac
            log_info "系统依赖安装完成!"
        else
            log_error "缺少必要的系统依赖,无法继续安装 FastAPI 部分"
            log_error "请手动安装以下依赖后重试:"
            for pkg in "${packages_to_install[@]}"; do
                echo "  - $pkg"
            done
            exit 1
        fi
    else
        log_info "系统依赖已满足!"
    fi
}

# 1. Spring 部分配置
setup_spring() {
    log_info "开始配置 Spring 部分..."
    
    cd "$WORKDIR/spring"
    
    # 同时使用 Gradle 和 Maven 安装依赖
    local spring_build_success=false
    
    if command_exists gradle; then
        log_info "使用 Gradle 构建 Spring..."
        if gradle clean build -x test; then
            log_info "Gradle 构建成功"
            spring_build_success=true
        else
            log_warn "Gradle 构建失败，尝试使用 Maven"
        fi
    fi
    
    if command_exists mvn; then
        log_info "使用 Maven 安装 Spring 依赖..."
        mvn clean install
        spring_build_success=true
    elif [ "$spring_build_success" = false ]; then
        log_warn "使用 mvnw 构建 Spring..."
        chmod +x mvnw
        ./mvnw clean install
    fi
    
    cd "$WORKDIR/gateway"
    
    # Gateway 同样同时使用 Gradle 和 Maven
    local gateway_build_success=false
    
    if command_exists gradle; then
        log_info "使用 Gradle 构建 Gateway..."
        if gradle clean build -x test; then
            log_info "Gradle 构建成功"
            gateway_build_success=true
        else
            log_warn "Gradle 构建失败，尝试使用 Maven"
        fi
    fi
    
    if command_exists mvn; then
        log_info "使用 Maven 安装 Gateway 依赖..."
        mvn clean install
        gateway_build_success=true
    elif [ "$gateway_build_success" = false ]; then
        log_info "使用 mvnw 构建 Gateway..."
        chmod +x mvnw
        ./mvnw clean install
    fi
    
    cd "$WORKDIR"
    log_info "Spring 部分配置完成!"
}

# 2. Gin 部分配置
setup_gin() {
    log_info "开始配置 Gin 部分..."
    
    cd "$WORKDIR/gin"
    
    # 安装依赖
    log_info "安装 Go 依赖..."
    go mod tidy
    
    # 安装 fresh 工具(可选)
    if ! command_exists fresh; then
        log_info "安装 fresh 热重载工具..."
        go install github.com/gravityblast/fresh@latest
    else
        log_info "fresh 工具已安装,跳过..."
    fi
    
    # 安装 swag 工具(可选)
    if ! command_exists swag; then
        log_info "安装 swag Swagger 工具..."
        go install github.com/swaggo/swag/cmd/swag@latest
        swag init
    else
        log_info "swag 工具已安装,更新 Swagger 文档..."
        swag init
    fi
    
    cd "$WORKDIR"
    log_info "Gin 部分配置完成!"
}

# 3. NestJS 部分配置
setup_nestjs() {
    log_info "开始配置 NestJS 部分..."
    
    cd "$WORKDIR/nestjs"
    
    # 检查并安装 Bun (可选)
    log_info "检查 NestJS 运行环境..."
    if command_exists bun; then
        log_info "使用 Bun 包管理器安装依赖..."
        bun install
    else
        log_info "使用 npm 安装依赖..."
        npm install
    fi
    
    cd "$WORKDIR"
    log_info "NestJS 部分配置完成!"
}

# 4. FastAPI 部分配置
setup_fastapi() {
    log_info "开始配置 FastAPI 部分..."
    
    # 检查并安装系统依赖
    check_and_install_system_deps
    
    cd "$WORKDIR/fastapi"
    
    # 检查 uv 是否已安装
    if ! command_exists uv; then
        log_info "安装 uv 包管理工具..."
        curl -LsSf https://astral.sh/uv/install.sh | sh
        export PATH="$HOME/.cargo/bin:$PATH"
        
        # 添加 uv 到 shell 配置文件
        log_info "配置 PATH 环境变量..."
        if [ -f "$HOME/.bashrc" ]; then
            if ! grep -q "\.cargo/bin" "$HOME/.bashrc"; then
                echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> "$HOME/.bashrc"
                log_info "已添加 uv PATH 到 ~/.bashrc"
            fi
        fi
        if [ -f "$HOME/.zshrc" ]; then
            if ! grep -q "\.cargo/bin" "$HOME/.zshrc"; then
                echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> "$HOME/.zshrc"
                log_info "已添加 uv PATH 到 ~/.zshrc"
            fi
        fi
    else
        log_info "uv 工具已安装"
    fi
    
    # 配置国内镜像源
    log_info "配置 uv 镜像源..."
    mkdir -p ~/.config/uv
    cat > ~/.config/uv/uv.toml << 'EOF'
[[index]]
name = "aliyun"
url = "https://mirrors.aliyun.com/pypi/simple"
default = true
EOF
    
    # 检查是否已有虚拟环境
    if [ -d ".venv" ]; then
        log_warn "检测到现有虚拟环境 .venv"
        echo "是否更新虚拟环境中的依赖? [y/N]"
        read -p "请输入: " update_venv
        
        if [[ "$update_venv" =~ ^[Yy]$ ]]; then
            log_info "更新 uv.lock 文件..."
            uv lock --upgrade
            
            log_info "同步依赖到虚拟环境..."
            uv sync
            log_info "虚拟环境更新完成!"
        else
            log_info "跳过虚拟环境更新"
            log_info "如需更新，可手动运行: cd fastapi && uv lock --upgrade && uv sync"
        fi
    else
        # 同步依赖
        log_info "使用 uv 同步依赖（创建新虚拟环境）..."
        uv sync
    fi
    
    cd "$WORKDIR"
    log_info "FastAPI 部分配置完成!"
}

# 检查必要的工具是否已安装
check_prerequisites() {
    log_info "检查系统环境..."
    
    local missing_tools=()
    
    # 检查 Python
    if ! command_exists python3; then
        missing_tools+=("Python 3.12+")
    else
        python_version=$(python3 --version | awk '{print $2}')
        log_info "Python 版本: $python_version"
    fi
    
    # 检查 Go
    if ! command_exists go; then
        missing_tools+=("Go 1.23+")
    else
        go_version=$(go version | awk '{print $3}')
        log_info "Go 版本: $go_version"
    fi
    
    # 检查 Java
    if ! command_exists java; then
        missing_tools+=("Java 17+")
    else
        java_version=$(java -version 2>&1 | head -n 1 | awk -F '"' '{print $2}')
        log_info "Java 版本: $java_version"
    fi
    
    # 检查 Node.js
    if ! command_exists node; then
        missing_tools+=("Node.js 20+")
    else
        node_version=$(node --version)
        log_info "Node.js 版本: $node_version"
    fi
    
    # 检查 npm
    if ! command_exists npm; then
        missing_tools+=("npm")
    else
        npm_version=$(npm --version)
        log_info "npm 版本: $npm_version"
    fi
    
    # 检查 Maven 或 Gradle (至少需要一个)
    if ! command_exists mvn && ! command_exists gradle; then
        missing_tools+=("Maven 或 Gradle (至少安装其中一个)")
    else
        if command_exists mvn; then
            mvn_version=$(mvn --version | head -n 1)
            log_info "$mvn_version"
        fi
    fi
    
    # 检查 Bun (可选)
    if ! command_exists bun; then
        log_warn "Bun 未安装"
    else
        bun_version=$(bun --version)
        log_info "Bun 版本: $bun_version"
    fi
    
    if [ ${#missing_tools[@]} -ne 0 ]; then
        log_error "以下工具未安装:"
        for tool in "${missing_tools[@]}"; do
            echo "  - $tool"
        done
        log_error "请先安装必要的工具后再运行此脚本"
        exit 1
    fi
    
    log_info "环境检查通过!"
}

# 检查 Gradle
check_gradle() {
    log_info "检查 Gradle..."
    
    if ! command_exists gradle; then
        log_warn "未检测到全局 Gradle (可选)"
        log_info "Gradle 用于加速 Spring/Gateway 构建"
        echo ""
        echo "安装 Gradle 的方法:"
        echo "  macOS (使用 Homebrew):"
        echo "    brew install gradle"
        echo ""
        echo "  Linux (Ubuntu/Debian):"
        echo "    sudo apt-get install gradle"
        echo ""
        echo "  Linux (CentOS/RHEL):"
        echo "    sudo yum install gradle"
        echo ""
        echo "  Linux (Arch):"
        echo "    sudo pacman -S gradle"
        echo ""
        echo "  或从官网下载: https://gradle.org/install/"
        echo ""
        log_warn "未安装 Gradle 时将使用 Maven 进行构建"
        return 0
    fi
    
    local gradle_version=$(gradle --version | head -n 1)
    log_info "Gradle 已安装: $gradle_version"
    return 0
}

# 检查并安装 Bun
check_and_install_bun() {
    if command_exists bun; then
        log_info "Bun 已安装,版本: $(bun --version)"
        return 0
    fi
    
    log_warn "未检测到 Bun,是否现在安装? [y/N]"
    read -p "请输入: " install_bun
    
    if [[ "$install_bun" =~ ^[Yy]$ ]]; then
        log_info "开始安装 Bun..."
        
        # 使用官方安装脚本
        curl -fsSL https://bun.sh/install | bash
        
        # 添加 Bun 到 PATH
        export BUN_INSTALL="$HOME/.bun"
        export PATH="$BUN_INSTALL/bin:$PATH"
        
        # 添加到 shell 配置文件
        if [ -f "$HOME/.bashrc" ]; then
            if ! grep -q "\.bun/bin" "$HOME/.bashrc"; then
                echo 'export BUN_INSTALL="$HOME/.bun"' >> "$HOME/.bashrc"
                echo 'export PATH="$BUN_INSTALL/bin:$PATH"' >> "$HOME/.bashrc"
                log_info "已添加 Bun PATH 到 ~/.bashrc"
            fi
        fi
        
        if [ -f "$HOME/.zshrc" ]; then
            if ! grep -q "\.bun/bin" "$HOME/.zshrc"; then
                echo 'export BUN_INSTALL="$HOME/.bun"' >> "$HOME/.zshrc"
                echo 'export PATH="$BUN_INSTALL/bin:$PATH"' >> "$HOME/.zshrc"
                log_info "已添加 Bun PATH 到 ~/.zshrc"
            fi
        fi
        
        # 验证安装
        if command_exists bun; then
            log_info "Bun 安装成功! 版本: $(bun --version)"
            return 0
        else
            log_error "Bun 安装失败,请手动安装或检查网络连接"
            return 1
        fi
    else
        log_warn "跳过 Bun 安装"
        return 0
    fi
}

# 创建必要的目录
create_directories() {
    log_info "创建必要的目录..."
    
    mkdir -p logs/spring
    mkdir -p logs/gin
    mkdir -p logs/nestjs
    mkdir -p logs/fastapi
    mkdir -p static/pic
    mkdir -p static/excel
    mkdir -p static/word
    
    log_info "目录创建完成!"
}

# 主函数
main() {
    log_info "========================================"
    log_info "多语言技术栈系统 - 依赖安装配置脚本"
    log_info "========================================"
    echo ""
    
    # 检测操作系统
    detect_os
    log_info "检测到操作系统: $OS"
    echo ""
    
    # 检查前置条件
    check_prerequisites
    echo ""
    
    # 检查 Gradle (可选)
    check_gradle
    echo ""
    
    # 创建目录
    create_directories
    echo ""
    
    # 检查并安装 Bun (可选)
    check_and_install_bun
    echo ""
    
    # 询问用户要配置哪些模块
    echo "请选择要配置的模块 (可多选,用空格分隔,例如: 1 2 3 4):"
    echo "1) Spring"
    echo "2) Gin"
    echo "3) NestJS"
    echo "4) FastAPI"
    echo "5) 全部"
    read -p "请输入选项: " choices
    
    echo ""
    
    # 处理用户选择
    if [[ "$choices" == *"5"* ]]; then
        setup_spring
        echo ""
        setup_gin
        echo ""
        setup_nestjs
        echo ""
        setup_fastapi
    else
        if [[ "$choices" == *"1"* ]]; then
            setup_spring
            echo ""
        fi
        if [[ "$choices" == *"2"* ]]; then
            setup_gin
            echo ""
        fi
        if [[ "$choices" == *"3"* ]]; then
            setup_nestjs
            echo ""
        fi
        if [[ "$choices" == *"4"* ]]; then
            setup_fastapi
            echo ""
        fi
    fi
    
    echo ""
    log_info "========================================"
    log_info "所有配置完成!"
    log_info "========================================"
    echo ""
    log_info "接下来请:"
    log_info "1. 配置各服务的 yaml 配置文件"
    log_info "2. 启动必要的基础服务 (MySQL, Redis, MongoDB 等)"
    log_info "3. 使用 ./services.sh multi 启动所有服务"
    echo ""
}

# 运行主函数
main

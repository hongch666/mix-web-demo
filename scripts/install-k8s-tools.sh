#!/bin/bash

# Kubernetes 工具安装脚本
# 用于安装kubectl、Minikube等K8s必要工具

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 打印函数
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查操作系统
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="linux"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
    else
        print_error "不支持的操作系统: $OSTYPE"
        exit 1
    fi
    
    # 检查CPU架构
    ARCH=$(uname -m)
    case $ARCH in
        x86_64)
            ARCH="amd64"
            ;;
        arm64)
            ARCH="arm64"
            ;;
        *)
            print_warning "可能不支持的架构: $ARCH"
            ;;
    esac
    
    print_info "检测到系统: $OS ($ARCH)"
}

# 安装kubectl
install_kubectl() {
    if command -v kubectl &> /dev/null; then
        local version=$(kubectl version --client --short 2>/dev/null)
        print_warning "kubectl已安装: $version"
        return 0
    fi
    
    print_info "安装kubectl..."
    
    local k8s_version=$(curl -s https://dl.k8s.io/release/stable.txt)
    print_info "下载版本: $k8s_version"
    
    local url="https://dl.k8s.io/release/$k8s_version/bin/$OS/$ARCH/kubectl"
    
    print_info "下载: $url"
    curl -LO "$url" || {
        print_error "下载失败"
        return 1
    }
    
    chmod +x kubectl
    
    if [ "$OS" = "linux" ]; then
        print_info "安装到系统路径..."
        sudo mv kubectl /usr/local/bin/ || {
            print_error "需要sudo权限"
            echo "请手动运行: sudo mv kubectl /usr/local/bin/"
            return 1
        }
    else
        sudo mv kubectl /usr/local/bin/ || {
            print_warning "请输入管理员密码"
            sudo mv kubectl /usr/local/bin/
        }
    fi
    
    print_success "kubectl安装完成"
    kubectl version --client --short
}

# 安装Minikube
install_minikube() {
    if command -v minikube &> /dev/null; then
        local version=$(minikube version)
        print_warning "Minikube已安装: $version"
        return 0
    fi
    
    print_info "安装Minikube..."
    
    if [ "$OS" = "linux" ]; then
        local url="https://github.com/kubernetes/minikube/releases/latest/download/minikube-linux-$ARCH"
    else
        local url="https://github.com/kubernetes/minikube/releases/latest/download/minikube-$OS-$ARCH"
    fi
    
    print_info "下载: $url"
    curl -LO "$url" || {
        print_error "下载失败"
        return 1
    }
    
    chmod +x "minikube-$OS-$ARCH"
    
    if [ "$OS" = "linux" ]; then
        print_info "安装到系统路径..."
        sudo mv "minikube-$OS-$ARCH" /usr/local/bin/minikube || {
            print_error "需要sudo权限"
            echo "请手动运行: sudo mv minikube-$OS-$ARCH /usr/local/bin/minikube"
            return 1
        }
    else
        sudo mv "minikube-$OS-$ARCH" /usr/local/bin/minikube
    fi
    
    print_success "Minikube安装完成"
    minikube version
}

# 安装Docker（如果需要）
install_docker() {
    if command -v docker &> /dev/null; then
        local version=$(docker --version)
        print_warning "Docker已安装: $version"
        return 0
    fi
    
    print_warning "Docker未安装"
    read -p "是否现在安装Docker? (y/n) " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_warning "跳过Docker安装"
        return 0
    fi
    
    print_info "安装Docker..."
    
    if [ "$OS" = "linux" ]; then
        if command -v apt-get &> /dev/null; then
            sudo apt-get update
            sudo apt-get install -y docker.io
        elif command -v yum &> /dev/null; then
            sudo yum install -y docker
        else
            print_error "不支持的包管理器"
            return 1
        fi
        
        # 启动Docker服务
        sudo systemctl start docker
        sudo systemctl enable docker
        
        # 配置用户权限
        sudo usermod -aG docker $USER
        print_warning "Docker已安装，请运行以下命令激活用户组:"
        echo "  newgrp docker"
    else
        print_warning "请访问 https://docs.docker.com/desktop/install/mac/ 安装Docker Desktop for Mac"
    fi
    
    print_success "Docker安装完成"
    docker --version
}

# 启动Minikube集群
start_minikube() {
    if minikube status &> /dev/null; then
        print_warning "Minikube集群已运行"
        return 0
    fi
    
    print_info "启动Minikube集群..."
    print_info "使用Docker驱动: minikube start --driver=docker"
    
    minikube start --driver=docker || {
        print_error "启动失败，请检查Docker是否正常运行"
        return 1
    }
    
    print_success "Minikube集群启动完成"
    minikube status
}

# 显示帮助信息
show_help() {
    cat << EOF
Kubernetes 工具安装脚本

用法: $0 [COMMAND]

命令:
  all              - 安装所有必要工具（kubectl + Docker + Minikube）
  kubectl          - 仅安装 kubectl
  minikube         - 仅安装 Minikube
  docker           - 仅安装 Docker
  start-cluster    - 启动 Minikube 集群
  help             - 显示此帮助信息

示例:
  # 安装所有工具
  $0 all

  # 安装并启动完整K8s环境
  $0 all
  $0 start-cluster

  # 仅安装kubectl
  $0 kubectl

说明:
  - 需要互联网连接以下载工具
  - Linux用户可能需要输入sudo密码
  - macOS需要安装Command Line Tools (xcode-select --install)

EOF
}

# 主函数
main() {
    print_info "Kubernetes工具安装脚本"
    print_info "检测系统信息..."
    
    detect_os
    
    local command=${1:-help}
    
    case $command in
        all)
            print_info "安装所有工具..."
            install_docker
            install_kubectl
            install_minikube
            print_success "所有工具安装完成！"
            print_info "后续步骤："
            echo "  1. 启动Minikube集群: $0 start-cluster"
            echo "  2. 加载Docker镜像到Minikube"
            echo "  3. 部署应用: ./services.sh k8s deploy"
            ;;
        kubectl)
            install_kubectl
            ;;
        minikube)
            install_minikube
            ;;
        docker)
            install_docker
            ;;
        start-cluster)
            start_minikube
            ;;
        help)
            show_help
            ;;
        *)
            print_error "未知命令: $command"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

main "$@"

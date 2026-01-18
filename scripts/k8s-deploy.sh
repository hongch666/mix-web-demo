#!/bin/bash

# Kubernetes 部署管理脚本
# 用于管理K8s资源的创建、删除、查看等操作

set -e

# 加载环境变量
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
K8S_DIR="$PROJECT_DIR/k8s"
NAMESPACE="mix-web-demo"

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

# 检查kubectl是否已安装
check_kubectl() {
    if ! command -v kubectl &> /dev/null; then
        print_error "kubectl未安装，请先安装kubectl"
        echo ""
        echo "安装方法："
        echo "  macOS: brew install kubectl"
        echo "  Linux: curl -LO \"https://dl.k8s.io/release/\$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl\""
        echo "  参考: https://kubernetes.io/docs/tasks/tools/"
        exit 1
    fi
}

# 检查是否连接到集群
check_cluster() {
    if ! kubectl cluster-info &> /dev/null; then
        print_error "无法连接到Kubernetes集群"
        echo ""
        echo "请确保已启动K8s集群，例如使用Minikube："
        echo "  minikube start"
        exit 1
    fi
}

# 检查K8s YAML文件是否存在
check_manifests() {
    if [ ! -d "$K8S_DIR" ]; then
        print_error "K8s配置文件目录不存在: $K8S_DIR"
        exit 1
    fi
    
    if [ ! -f "$K8S_DIR/namespace.yaml" ]; then
        print_error "缺少必要的配置文件: $K8S_DIR/namespace.yaml"
        exit 1
    fi
}

# 部署应用到K8s
deploy() {
    print_info "检查环境..."
    check_kubectl
    check_cluster
    check_manifests
    
    print_info "创建命名空间..."
    kubectl apply -f "$K8S_DIR/namespace.yaml" || true
    
    print_info "创建配置文件..."
    kubectl apply -f "$K8S_DIR/configmap.yaml"
    
    print_info "部署应用..."
    kubectl apply -f "$K8S_DIR/deployment.yaml"
    
    print_info "部署Ingress..."
    kubectl apply -f "$K8S_DIR/ingress.yaml" || print_warning "Ingress部署失败（可能需要安装Ingress控制器）"
    
    print_success "应用部署完成！"
    echo ""
    print_info "查看部署状态："
    echo "  kubectl get deployment -n $NAMESPACE"
    echo "  kubectl get pods -n $NAMESPACE"
}

# 删除应用
delete() {
    print_warning "即将删除所有K8s资源..."
    read -p "是否继续? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "删除Ingress..."
        kubectl delete -f "$K8S_DIR/ingress.yaml" --ignore-not-found=true
        
        print_info "删除Deployment和Service..."
        kubectl delete -f "$K8S_DIR/deployment.yaml" --ignore-not-found=true
        
        print_info "删除ConfigMap..."
        kubectl delete -f "$K8S_DIR/configmap.yaml" --ignore-not-found=true
        
        print_info "删除Namespace..."
        kubectl delete -f "$K8S_DIR/namespace.yaml" --ignore-not-found=true
        
        print_success "资源删除完成！"
    else
        print_info "取消删除操作"
    fi
}

# 查看部署状态
status() {
    check_kubectl
    
    print_info "Deployment状态:"
    kubectl get deployment -n $NAMESPACE -o wide
    
    echo ""
    print_info "Pods状态:"
    kubectl get pods -n $NAMESPACE -o wide
    
    echo ""
    print_info "Services:"
    kubectl get svc -n $NAMESPACE -o wide
}

# 查看资源详细信息
describe() {
    check_kubectl
    
    if [ -z "$1" ]; then
        print_error "请指定资源类型: deployment, pod, service, ingress"
        exit 1
    fi
    
    kubectl describe "$1" -n $NAMESPACE
}

# 查看Pod日志
logs() {
    check_kubectl
    
    if [ -z "$1" ]; then
        print_error "请指定Pod名称或标签"
        echo "用法: $0 logs <pod_name>"
        echo "或者: $0 logs <service_name> (显示该服务的日志)"
        exit 1
    fi
    
    # 查找匹配的Pod
    local pods=$(kubectl get pods -n $NAMESPACE -l "app=$1" -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
    
    if [ -z "$pods" ]; then
        print_error "未找到匹配的Pod: $1"
        exit 1
    fi
    
    print_info "显示Pod [$pods] 的日志:"
    kubectl logs -f "$pods" -n $NAMESPACE
}

# 进入Pod交互式终端
exec() {
    check_kubectl
    
    if [ -z "$1" ]; then
        print_error "请指定Pod名称或服务名称"
        echo "用法: $0 exec <pod_name_or_service_name>"
        exit 1
    fi
    
    # 查找匹配的Pod
    local pods=$(kubectl get pods -n $NAMESPACE -l "app=$1" -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
    
    if [ -z "$pods" ]; then
        print_error "未找到匹配的Pod: $1"
        exit 1
    fi
    
    print_info "进入Pod [$pods] 的交互式终端:"
    kubectl exec -it "$pods" -n $NAMESPACE -- /bin/sh
}

# 端口转发
port_forward() {
    check_kubectl
    
    if [ -z "$1" ] || [ -z "$2" ]; then
        print_error "请指定服务名称和端口"
        echo "用法: $0 port-forward <service_name> <local_port>:<pod_port>"
        echo "示例:"
        echo "  $0 port-forward gin 8081:8081"
        echo "  $0 port-forward spring 8083:8083"
        exit 1
    fi
    
    local service=$1
    local port=$2
    
    print_info "启动端口转发: localhost:$port -> $service (Pods)"
    print_info "按Ctrl+C停止转发"
    
    kubectl port-forward "svc/$service" "$port" -n $NAMESPACE
}

# 重启Deployment
restart() {
    check_kubectl
    
    if [ -z "$1" ]; then
        print_error "请指定Deployment名称"
        echo "可用的Deployment: gin, nestjs, spring, gateway, fastapi"
        exit 1
    fi
    
    print_info "重启Deployment: $1"
    kubectl rollout restart deployment "$1" -n $NAMESPACE
    
    print_success "Deployment已重启"
}

# 查看滚动更新状态
rollout_status() {
    check_kubectl
    
    if [ -z "$1" ]; then
        print_error "请指定Deployment名称"
        exit 1
    fi
    
    kubectl rollout status deployment "$1" -n $NAMESPACE
}

# 显示帮助信息
show_help() {
    cat << EOF
Kubernetes 部署管理脚本

用法: $0 [COMMAND] [OPTIONS]

命令:
  deploy              - 部署应用到K8s集群
  delete              - 删除K8s中的所有资源
  status              - 查看部署状态
  describe [TYPE]     - 查看资源详细信息 (deployment/pod/service/ingress)
  logs [SERVICE]      - 查看Pod日志 (SERVICE: gin/nestjs/spring/gateway/fastapi)
  exec [SERVICE]      - 进入Pod交互式终端
  port-forward [SERVICE] [PORT] - 进行端口转发
  restart [SERVICE]   - 重启Deployment
  rollout-status [SERVICE] - 查看滚动更新状态
  help                - 显示此帮助信息

示例:
  # 部署应用
  $0 deploy

  # 查看状态
  $0 status

  # 查看Gin服务的日志
  $0 logs gin

  # 进入Spring Pod交互式终端
  $0 exec spring

  # 本地访问FastAPI服务
  $0 port-forward fastapi 8084:8084

  # 重启NestJS服务
  $0 restart nestjs

  # 查看Spring服务的滚动更新状态
  $0 rollout-status spring

前置要求:
  - kubectl (Kubernetes客户端工具)
  - 一个运行中的Kubernetes集群 (例如Minikube、Docker Desktop K8s等)
  - 已构建的Docker镜像 (mix-gin, mix-nestjs, mix-spring, mix-gateway, mix-fastapi)

安装Minikube:
  macOS: brew install minikube
  Linux: curl -LO https://github.com/kubernetes/minikube/releases/download/latest/minikube-linux-amd64
  参考: https://minikube.sigs.k8s.io/docs/start/

启动Minikube:
  minikube start --driver=docker
  minikube dashboard # 打开仪表板

加载本地Docker镜像到Minikube:
  eval \$(minikube docker-env)
  docker build -t mix-gin:latest ./gin
  docker build -t mix-nestjs:latest ./nestjs
  docker build -t mix-spring:latest ./spring
  docker build -t mix-gateway:latest ./gateway
  docker build -t mix-fastapi:latest ./fastapi

EOF
}

# 主函数
main() {
    local command=${1:-help}
    
    case $command in
        deploy)
            deploy
            ;;
        delete)
            delete
            ;;
        status)
            status
            ;;
        describe)
            describe "$2"
            ;;
        logs)
            logs "$2"
            ;;
        exec)
            exec "$2"
            ;;
        port-forward)
            port_forward "$2" "$3"
            ;;
        restart)
            restart "$2"
            ;;
        rollout-status)
            rollout_status "$2"
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

#!/bin/bash

# 统一控制脚本 - 启动/停止所有打包后的微服务
# 使用方式: ./dist-control.sh [start|stop|restart|status] [service1 service2 ...]

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT=$(pwd)
DIST_DIR="$PROJECT_ROOT/dist"

# 服务端口配置（根据实际配置修改）
declare -A SERVICE_PORTS=(
    ["spring"]="8081"
    ["gateway"]="8080"
    ["fastapi"]="8084"
    ["gin"]="8082"
    ["nestjs"]="8083"
)

# 服务进程特征（用于 pgrep 匹配）
declare -A SERVICE_PATTERNS=(
    ["spring"]="spring.jar"
    ["gateway"]="gateway.jar"
    ["fastapi"]="fastapi.*main.py|uvicorn.*fastapi"
    ["gin"]="gin_service"
    ["nestjs"]="nestjs.*main.js|node.*nestjs"
)

# 打印带颜色的消息
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_status() {
    echo -e "${BLUE}[STATUS]${NC} $1"
}

# 检查端口是否被占用，返回占用该端口的 PID
check_port_in_use() {
    local port=$1
    local pid=$(lsof -t -i:$port 2>/dev/null | head -1)
    if [ -n "$pid" ]; then
        echo "$pid"
    else
        echo ""
    fi
}

# 通过进程名模式查找进程
find_process_by_pattern() {
    local pattern=$1
    local pid=$(pgrep -f "$pattern" 2>/dev/null | head -1)
    if [ -n "$pid" ]; then
        echo "$pid"
    else
        echo ""
    fi
}

# 检查服务状态（综合判断：PID文件 + 端口检测 + 进程匹配）
check_service_status() {
    local service=$1
    local service_dir="$DIST_DIR/$service"
    local port="${SERVICE_PORTS[$service]}"
    local pattern="${SERVICE_PATTERNS[$service]}"
    
    if [ ! -d "$service_dir" ]; then
        echo "not_found"
        return
    fi
    
    cd "$service_dir"
    
    local pid=""
    local source=""
    
    # 方法1: 检查 PID 文件
    if [ -f "${service}.pid" ]; then
        local file_pid=$(cat "${service}.pid")
        if ps -p $file_pid > /dev/null 2>&1; then
            pid=$file_pid
            source="pid_file"
        fi
    fi
    
    # 方法2: 如果 PID 文件无效，通过端口检测
    if [ -z "$pid" ] && [ -n "$port" ]; then
        local port_pid=$(check_port_in_use "$port")
        if [ -n "$port_pid" ]; then
            pid=$port_pid
            source="port"
        fi
    fi
    
    # 方法3: 如果端口也没找到，通过进程模式匹配
    if [ -z "$pid" ] && [ -n "$pattern" ]; then
        local pattern_pid=$(find_process_by_pattern "$pattern")
        if [ -n "$pattern_pid" ]; then
            pid=$pattern_pid
            source="pattern"
        fi
    fi
    
    if [ -n "$pid" ]; then
        echo "running:$pid:$source"
    else
        echo "stopped"
    fi
}

# 启动服务
start_service() {
    local service=$1
    local service_dir="$DIST_DIR/$service"
    
    if [ ! -d "$service_dir" ]; then
        print_error "服务目录不存在: $service_dir"
        return 1
    fi
    
    local status=$(check_service_status "$service")
    if [[ $status == running:* ]]; then
        local pid=$(echo "$status" | cut -d: -f2)
        print_warn "$service 服务已在运行中 (PID: $pid)"
        return 0
    fi
    
    print_info "启动 $service 服务..."
    cd "$service_dir"
    
    if [ -f "start.sh" ]; then
        bash start.sh
        sleep 2
        
        # 验证启动
        status=$(check_service_status "$service")
        if [[ $status == running:* ]]; then
            local pid=$(echo "$status" | cut -d: -f2)
            print_info "$service 服务启动成功 (PID: $pid)"
        else
            print_error "$service 服务启动失败，请查看日志"
            return 1
        fi
    else
        print_error "未找到启动脚本: start.sh"
        return 1
    fi
}

# 停止服务
stop_service() {
    local service=$1
    local service_dir="$DIST_DIR/$service"
    
    if [ ! -d "$service_dir" ]; then
        print_error "服务目录不存在: $service_dir"
        return 1
    fi
    
    local status=$(check_service_status "$service")
    if [[ $status == "stopped" ]]; then
        print_warn "$service 服务未运行"
        return 0
    fi
    
    # 提取真实的 PID
    local pid=$(echo "$status" | cut -d: -f2)
    local source=$(echo "$status" | cut -d: -f3)
    
    print_info "停止 $service 服务 (PID: $pid, 检测方式: $source)..."
    cd "$service_dir"
    
    # 直接使用检测到的 PID 来停止进程
    if [ -n "$pid" ]; then
        kill $pid 2>/dev/null || true
        sleep 1
        
        # 如果进程还在，强制杀死
        if ps -p $pid > /dev/null 2>&1; then
            print_warn "进程未响应，强制终止..."
            kill -9 $pid 2>/dev/null || true
        fi
        
        # 清理 PID 文件
        rm -f "${service}.pid"
    fi
    
    sleep 1
    
    # 验证停止
    status=$(check_service_status "$service")
    if [[ $status == "stopped" ]]; then
        print_info "$service 服务已停止"
    else
        print_warn "$service 服务可能未完全停止"
    fi
}

# 重启服务
restart_service() {
    local service=$1
    print_info "重启 $service 服务..."
    stop_service "$service"
    sleep 2
    start_service "$service"
}

# 显示服务状态
show_status() {
    local services=("$@")
    
    if [ ${#services[@]} -eq 0 ]; then
        # 默认显示所有服务
        services=("spring" "gateway" "fastapi" "gin" "nestjs")
    fi
    
    print_info "=========================================="
    print_info "微服务运行状态"
    print_info "=========================================="
    
    printf "%-15s %-15s %-10s %-10s\n" "服务名称" "状态" "PID" "检测方式"
    echo "---------------------------------------------------"
    
    for service in "${services[@]}"; do
        local status=$(check_service_status "$service")
        
        case "$status" in
            running:*)
                local pid=$(echo "$status" | cut -d: -f2)
                local source=$(echo "$status" | cut -d: -f3)
                local source_text=""
                case "$source" in
                    pid_file) source_text="PID文件" ;;
                    port) source_text="端口检测" ;;
                    pattern) source_text="进程匹配" ;;
                esac
                printf "%-15s ${GREEN}%-15s${NC} %-10s %-10s\n" "$service" "运行中" "$pid" "$source_text"
                ;;
            stopped)
                printf "%-15s ${RED}%-15s${NC} %-10s %-10s\n" "$service" "已停止" "-" "-"
                ;;
            not_found)
                printf "%-15s ${YELLOW}%-15s${NC} %-10s %-10s\n" "$service" "未安装" "-" "-"
                ;;
        esac
    done
    
    echo "==================================================="
}

# 查看日志
view_logs() {
    local service=$1
    local logs_dir="$DIST_DIR/logs/$service"
    
    if [ ! -d "$logs_dir" ]; then
        print_error "日志目录不存在: $logs_dir"
        return 1
    fi
    
    # 获取最新的日志文件 (app_YYYY-MM-DD.log 格式)
    local latest_log=$(ls -t "$logs_dir"/app_*.log 2>/dev/null | head -1)
    
    if [ -z "$latest_log" ]; then
        print_warn "未找到日志文件"
        return 1
    fi
    
    print_info "显示 $service 服务日志（最后100行）："
    print_info "日志文件: $latest_log"
    echo "-------------------------------------------"
    tail -100 "$latest_log"
}

# 使用说明
show_usage() {
    cat << EOF
使用方式: $0 <command> [services...]

命令:
  start       启动服务
  stop        停止服务
  restart     重启服务
  status      查看服务状态
  logs        查看服务日志

服务名称（可选，不指定则操作所有服务）:
  spring      Spring Boot 服务
  gateway     Spring Cloud Gateway 服务
  fastapi     FastAPI 服务
  gin         Gin 服务
  nestjs      NestJS 服务

示例:
  $0 start                    # 启动所有服务
  $0 start spring gateway     # 启动指定服务
  $0 stop                     # 停止所有服务
  $0 restart fastapi          # 重启 FastAPI 服务
  $0 status                   # 查看所有服务状态
  $0 logs spring              # 查看 Spring 服务日志

注意: 请先执行 ./build.sh 打包所有服务
EOF
}

# 主函数
main() {
    if [ $# -eq 0 ]; then
        show_usage
        exit 1
    fi
    
    local command=$1
    shift
    
    local services=("$@")
    
    # 如果没有指定服务，默认操作所有服务
    if [ ${#services[@]} -eq 0 ]; then
        services=("spring" "gateway" "fastapi" "gin" "nestjs")
    fi
    
    case "$command" in
        start)
            for service in "${services[@]}"; do
                start_service "$service"
                echo ""
            done
            echo ""
            show_status "${services[@]}"
            ;;
        stop)
            for service in "${services[@]}"; do
                stop_service "$service"
                echo ""
            done
            echo ""
            show_status "${services[@]}"
            ;;
        restart)
            for service in "${services[@]}"; do
                restart_service "$service"
                echo ""
            done
            echo ""
            show_status "${services[@]}"
            ;;
        status)
            show_status "${services[@]}"
            ;;
        logs)
            if [ ${#services[@]} -eq 1 ]; then
                view_logs "${services[0]}"
            else
                print_error "logs 命令只能查看单个服务的日志"
                exit 1
            fi
            ;;
        *)
            print_error "未知命令: $command"
            show_usage
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"

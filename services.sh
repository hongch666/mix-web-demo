#!/bin/bash

# 脚本说明：
# 这是根目录下的便捷启动脚本，用于快速启动项目

WORKDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPTS_DIR="$WORKDIR/scripts"

# 确保scripts目录存在
if [ ! -d "$SCRIPTS_DIR" ]; then
    echo "Error: scripts directory not found at $SCRIPTS_DIR"
    exit 1
fi

# 显示帮助信息
show_help() {
    echo "================================"
    echo "Mix Web Demo - Service Launcher"
    echo "================================"
    echo ""
    echo "Usage: ./services.sh <COMMAND> [SERVICE_NAME] [SERVICE_NAME] ..."
    echo ""
    echo "Development Commands (开发模式):"
    echo "  multi                    - Run all services in tmux with split panes"
    echo "  seq                      - Run all services in tmux (sequential window mode)"
    echo "  stop                     - Stop all tmux sessions"
    echo ""
    echo "Build & Deploy Commands (编译部署):"
    echo "  build                    - Build all services to dist/"
    echo "  start [services...]      - Start built services (or all if not specified)"
    echo "  stop-dist [services...]  - Stop built services (or all if not specified)"
    echo "  restart [services...]    - Restart built services (or all if not specified)"
    echo "  status [services...]     - Check status of services (or all if not specified)"
    echo "  logs <service>           - View latest logs of a specific service"
    echo ""
    echo "Setup Commands (初始化):"
    echo "  setup                    - Initialize environment and install dependencies"
    echo ""
    echo "Other:"
    echo "  help                     - Show this help message"
    echo ""
    echo "Service Names (服务名称):"
    echo "  spring                   - Spring Boot 服务"
    echo "  gateway                  - Spring Cloud Gateway 服务"
    echo "  fastapi                  - FastAPI 服务"
    echo "  gin                      - Gin 服务"
    echo "  nestjs                   - NestJS 服务"
    echo ""
    echo "Examples (示例):"
    echo "  ./services.sh setup                    # Initialize environment (first time)"
    echo "  ./services.sh multi                    # Multi-pane tmux layout (dev)"
    echo "  ./services.sh seq                      # Sequential window layout (dev)"
    echo "  ./services.sh stop                     # Stop tmux sessions (dev)"
    echo "  ./services.sh build                    # Build all services"
    echo "  ./services.sh start                    # Start all built services"
    echo "  ./services.sh start spring gin         # Start specific services"
    echo "  ./services.sh restart fastapi          # Restart FastAPI service"
    echo "  ./services.sh status                   # Check status of all services"
    echo "  ./services.sh status spring gateway    # Check status of specific services"
    echo "  ./services.sh logs spring              # View Spring service logs"
    echo "  ./services.sh stop-dist                # Stop all services"
    echo "  ./services.sh stop-dist fastapi nestjs # Stop specific services"
    echo ""
    echo "Notes (备注):"
    echo "  - For Windows PowerShell: PowerShell -ExecutionPolicy Bypass -File ./scripts/run.ps1"
    echo "  - Direct script calls are also supported: ./scripts/run_multi.sh"
    echo "  - Use 'logs' command with exactly one service name"
    echo ""
}

# 解析命令参数
COMMAND=${1:-help}
shift || true

case $COMMAND in
    setup)
        echo "Initializing environment and installing dependencies..."
        bash "$SCRIPTS_DIR/setup.sh"
        ;;
    multi)
        echo "Starting services in multi-pane layout..."
        bash "$SCRIPTS_DIR/run_multi.sh"
        ;;
    seq)
        echo "Starting services in sequential window layout..."
        bash "$SCRIPTS_DIR/run.sh"
        ;;
    stop)
        echo "Stopping all tmux sessions..."
        bash "$SCRIPTS_DIR/stop.sh"
        ;;
    build)
        echo "Building all services..."
        bash "$SCRIPTS_DIR/build.sh"
        ;;
    start)
        if [ $# -eq 0 ]; then
            echo "Starting all built services..."
            bash "$SCRIPTS_DIR/dist-control.sh" start
        else
            echo "Starting specified services: $@"
            bash "$SCRIPTS_DIR/dist-control.sh" start "$@"
        fi
        ;;
    stop-dist)
        if [ $# -eq 0 ]; then
            echo "Stopping all built services..."
            bash "$SCRIPTS_DIR/dist-control.sh" stop
        else
            echo "Stopping specified services: $@"
            bash "$SCRIPTS_DIR/dist-control.sh" stop "$@"
        fi
        ;;
    restart)
        if [ $# -eq 0 ]; then
            echo "Restarting all built services..."
            bash "$SCRIPTS_DIR/dist-control.sh" restart
        else
            echo "Restarting specified services: $@"
            bash "$SCRIPTS_DIR/dist-control.sh" restart "$@"
        fi
        ;;
    status)
        if [ $# -eq 0 ]; then
            echo "Checking all services status..."
            bash "$SCRIPTS_DIR/dist-control.sh" status
        else
            echo "Checking specified services status: $@"
            bash "$SCRIPTS_DIR/dist-control.sh" status "$@"
        fi
        ;;
    logs)
        if [ $# -eq 0 ]; then
            echo "Error: 'logs' command requires a service name"
            echo "Usage: ./services.sh logs <service_name>"
            echo ""
            echo "Example: ./services.sh logs spring"
            exit 1
        elif [ $# -gt 1 ]; then
            echo "Error: 'logs' command only accepts one service name"
            exit 1
        else
            echo "Viewing logs for service: $1"
            bash "$SCRIPTS_DIR/dist-control.sh" logs "$1"
        fi
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo "Unknown command: $COMMAND"
        echo ""
        show_help
        exit 1
        ;;
esac

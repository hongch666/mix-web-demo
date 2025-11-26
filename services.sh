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
    echo "Usage: ./services.sh [COMMAND]"
    echo ""
    echo "Commands (Setup & Config):"
    echo "  setup    - Initialize environment and install dependencies"
    echo ""
    echo "Commands (Development):"
    echo "  multi    - Run all services in tmux with split panes"
    echo "  seq      - Run all services in tmux (sequential window mode)"
    echo "  stop     - Stop all tmux sessions"
    echo ""
    echo "Commands (Build & Deploy):"
    echo "  build    - Build all services to dist/"
    echo "  start    - Start all built services from dist/"
    echo "  status   - Check status of all built services"
    echo "  restart  - Restart all built services"
    echo "  stop-dist - Stop all built services"
    echo ""
    echo "Other:"
    echo "  help     - Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./services.sh setup              # Initialize environment (first time)"
    echo "  ./services.sh multi              # Multi-pane tmux layout (dev)"
    echo "  ./services.sh seq                # Sequential window layout (dev)"
    echo "  ./services.sh stop               # Stop tmux sessions (dev)"
    echo "  ./services.sh build              # Build all services"
    echo "  ./services.sh start              # Start built services"
    echo "  ./services.sh status             # Check service status"
    echo "  ./services.sh restart            # Restart built services"
    echo ""
    echo "Notes:"
    echo "  - For Windows PowerShell: PowerShell -ExecutionPolicy Bypass -File ./scripts/run.ps1"
    echo "  - Direct script calls are also supported: ./scripts/run_multi.sh"
    echo ""
}

# 解析命令参数
COMMAND=${1:-help}

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
        echo "Stopping all services..."
        bash "$SCRIPTS_DIR/stop.sh"
        ;;
    build)
        echo "Building all services..."
        bash "$SCRIPTS_DIR/build.sh"
        ;;
    start)
        echo "Starting all built services..."
        bash "$SCRIPTS_DIR/dist-control.sh" start
        ;;
    stop-dist)
        echo "Stopping all built services..."
        bash "$SCRIPTS_DIR/dist-control.sh" stop
        ;;
    status)
        echo "Checking built services status..."
        bash "$SCRIPTS_DIR/dist-control.sh" status
        ;;
    restart)
        echo "Restarting all built services..."
        bash "$SCRIPTS_DIR/dist-control.sh" restart
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

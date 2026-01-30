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
    echo "  seq [OPTIONS]            - Run all services in tmux (sequential window mode)"
    echo "  stop                     - Stop all tmux sessions"
    echo ""
    echo "Seq Options (用于 seq 命令的可选项):"
    echo "  -i, --interactive        - 进入交互式选择模式"
    echo "  --java-build TOOL        - Java 构建工具: gradle(默认)|maven"
    echo "  --node-runtime TOOL      - Node.js 运行时: bun(默认)|npm"
    echo "  --python-runtime TOOL    - Python 运行时: uv(默认)|python"
    echo ""
    echo "Seq Examples:"
    echo "  ./services.sh seq                     # 使用默认配置 (gradle+bun+uv)"
    echo "  ./services.sh seq -i                  # 交互式选择"
    echo "  ./services.sh seq --java-build maven --node-runtime npm"
    echo ""
    echo "Build & Deploy Commands (编译部署):"
    echo "  build                    - Build all services to dist/"
    echo "  start [services...]      - Start built services (or all if not specified)"
    echo "  stop-dist [services...]  - Stop built services (or all if not specified)"
    echo "  restart [services...]    - Restart built services (or all if not specified)"
    echo "  status [services...]     - Check status of services (or all if not specified)"
    echo "  logs <service>           - View latest logs of a specific service"
    echo ""
    echo "Docker Commands (Docker 容器管理):"
    echo "  docker [command]         - Manage Docker containers"
    echo "    up [services...]       - Build and run containers (or all if not specified)"
    echo "    build [services...]    - Build images only"
    echo "    status                 - Show container status"
    echo "    logs <service>         - View container logs"
    echo "    stop                   - Stop all containers"
    echo "    delete                 - Delete all containers"
    echo ""
    echo "Kubernetes Commands (K8s 集群管理):"
    echo "  k8s [command] [args]     - Manage Kubernetes deployment"
    echo "    deploy                 - Deploy all services to K8s"
    echo "    delete                 - Delete all K8s resources"
    echo "    status                 - Show deployment/pod/service status"
    echo "    logs <service>         - View pod logs of a service"
    echo "    exec <service>         - Execute shell in service pod"
    echo "    port-forward <service> <port> - Forward local port to service"
    echo "    restart <service>      - Rolling restart a service"
    echo "    describe <service>     - Show detailed info about service"
    echo "    install                - Install/check K8s tools"
    echo "    help                   - Show K8s help message"
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
    echo "  ./services.sh seq                      # Sequential window layout (dev, default config)"
    echo "  ./services.sh seq -i                   # Sequential layout with interactive mode"
    echo "  ./services.sh seq --java-build maven   # Use Maven for Java services"
    echo "  ./services.sh seq --node-runtime npm   # Use NPM for Node.js"
    echo "  ./services.sh seq --python-runtime python  # Use Python for FastAPI"
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
    echo "  ./services.sh docker up                # Build and run all containers"
    echo "  ./services.sh docker up spring gin     # Build and run specific containers"
    echo "  ./services.sh docker build             # Build all images only"
    echo "  ./services.sh docker status            # Show container status"
    echo "  ./services.sh docker logs spring       # View Spring container logs"
    echo "  ./services.sh docker stop              # Stop all containers"
    echo ""
    echo "Notes (备注):"
    echo "  - For Windows PowerShell: PowerShell -ExecutionPolicy Bypass -File ./scripts/run.ps1"
    echo "  - Direct script calls are also supported: ./scripts/run_multi.sh"
    echo "  - Use 'logs' command with exactly one service name"
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
        # 将所有额外参数传递给 run.sh
        bash "$SCRIPTS_DIR/run.sh" "${@:2}"
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
        if [ $# -le 1 ]; then
            echo "Starting all built services..."
            bash "$SCRIPTS_DIR/dist-control.sh" start
        else
            echo "Starting specified services: ${@:2}"
            bash "$SCRIPTS_DIR/dist-control.sh" start "${@:2}"
        fi
        ;;
    stop-dist)
        if [ $# -le 1 ]; then
            echo "Stopping all built services..."
            bash "$SCRIPTS_DIR/dist-control.sh" stop
        else
            echo "Stopping specified services: ${@:2}"
            bash "$SCRIPTS_DIR/dist-control.sh" stop "${@:2}"
        fi
        ;;
    restart)
        if [ $# -le 1 ]; then
            echo "Restarting all built services..."
            bash "$SCRIPTS_DIR/dist-control.sh" restart
        else
            echo "Restarting specified services: ${@:2}"
            bash "$SCRIPTS_DIR/dist-control.sh" restart "${@:2}"
        fi
        ;;
    status)
        if [ $# -le 1 ]; then
            echo "Checking all services status..."
            bash "$SCRIPTS_DIR/dist-control.sh" status
        else
            echo "Checking specified services status: ${@:2}"
            bash "$SCRIPTS_DIR/dist-control.sh" status "${@:2}"
        fi
        ;;
    logs)
        if [ $# -le 1 ]; then
            echo "Error: 'logs' command requires a service name"
            echo "Usage: ./services.sh logs <service_name>"
            echo ""
            echo "Example: ./services.sh logs spring"
            exit 1
        elif [ $# -gt 2 ]; then
            echo "Error: 'logs' command only accepts one service name"
            exit 1
        else
            echo "Viewing logs for service: $2"
            bash "$SCRIPTS_DIR/dist-control.sh" logs "$2"
        fi
        ;;
    docker)
        if [ $# -lt 2 ]; then
            # 默认执行up命令
            echo "Building and running all Docker containers..."
            bash "$SCRIPTS_DIR/build_and_run_services.sh"
        else
            case $2 in
                up)
                    if [ $# -le 2 ]; then
                        echo "Building and running all Docker containers..."
                        bash "$SCRIPTS_DIR/build_and_run_services.sh"
                    else
                        echo "Building and running specified services: ${@:3}"
                        bash "$SCRIPTS_DIR/build_and_run_services.sh" "${@:3}"
                    fi
                    ;;
                build)
                    if [ $# -le 2 ]; then
                        echo "Building all Docker images..."
                        bash "$SCRIPTS_DIR/build_and_run_services.sh" --build-only
                    else
                        echo "Building specified images: ${@:3}"
                        bash "$SCRIPTS_DIR/build_and_run_services.sh" --build-only "${@:3}"
                    fi
                    ;;
                status)
                    echo "Showing Docker container status..."
                    bash "$SCRIPTS_DIR/build_and_run_services.sh" --status
                    ;;
                logs)
                    if [ $# -le 2 ]; then
                        echo "Error: 'docker logs' requires a service name"
                        exit 1
                    else
                        docker logs -f "mix-$3-container"
                    fi
                    ;;
                stop)
                    echo "Stopping all Docker containers..."
                    bash "$SCRIPTS_DIR/build_and_run_services.sh" --clean
                    ;;
                delete)
                    echo "Deleting all Docker containers..."
                    bash "$SCRIPTS_DIR/build_and_run_services.sh" --clean
                    ;;
                *)
                    echo "Unknown docker command: $2"
                    exit 1
                    ;;
            esac
        fi
        ;;
    k8s)
        if [ $# -lt 2 ]; then
            bash "$SCRIPTS_DIR/k8s-deploy.sh" help
        else
            bash "$SCRIPTS_DIR/k8s-deploy.sh" "$@"
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

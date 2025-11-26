#!/bin/bash

# 获取脚本所在目录的父目录（项目根目录）
WORKDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIST_DIR="$WORKDIR/dist"

# 检查dist目录是否存在
if [ ! -d "$DIST_DIR" ]; then
    echo "Error: dist directory not found. Please run 'scripts/build.sh' first."
    exit 1
fi

# 操作类型
ACTION=${1:-status}

case $ACTION in
    start)
        echo "Starting distributed services..."
        
        # Spring
        echo "Starting Spring service..."
        cd "$DIST_DIR/spring"
        (./mvnw spring-boot:run > "$WORKDIR/logs/spring/dist.log" 2>&1 &)
        sleep 2
        
        # Gateway
        echo "Starting Gateway..."
        cd "$DIST_DIR/gateway"
        (./mvnw spring-boot:run > "$WORKDIR/logs/gateway/dist.log" 2>&1 &)
        sleep 2
        
        # Gin (Go-Zero)
        echo "Starting Go-Zero service..."
        cd "$DIST_DIR/gozero"
        (./gozero_service -f etc/gozero-api.yaml > "$WORKDIR/logs/gozero/dist.log" 2>&1 &)
        sleep 2
        
        # NestJS
        echo "Starting NestJS service..."
        cd "$DIST_DIR/nestjs"
        (npm run start > "$WORKDIR/logs/nestjs/dist.log" 2>&1 &)
        sleep 2
        
        # FastAPI
        echo "Starting FastAPI service..."
        cd "$DIST_DIR/fastapi"
        (uv run python main.py > "$WORKDIR/logs/fastapi/dist.log" 2>&1 &)
        
        echo "All services started!"
        ;;
        
    stop)
        echo "Stopping all services..."
        pkill -f "mvnw spring-boot:run"
        pkill -f "gozero_service"
        pkill -f "npm run start"
        pkill -f "uv run python main.py"
        echo "All services stopped!"
        ;;
        
    status)
        echo "Checking service status..."
        echo ""
        echo "Spring:"
        ps aux | grep "mvnw spring-boot:run" | grep -v grep || echo "  Not running"
        echo ""
        echo "Gateway:"
        ps aux | grep "gateway.*spring-boot:run" | grep -v grep || echo "  Not running"
        echo ""
        echo "Go-Zero:"
        ps aux | grep "gozero_service" | grep -v grep || echo "  Not running"
        echo ""
        echo "NestJS:"
        ps aux | grep "npm run start" | grep -v grep || echo "  Not running"
        echo ""
        echo "FastAPI:"
        ps aux | grep "uv run python main.py" | grep -v grep || echo "  Not running"
        ;;
        
    restart)
        $0 stop
        sleep 2
        $0 start
        ;;
        
    *)
        echo "Usage: $0 {start|stop|status|restart}"
        exit 1
        ;;
esac

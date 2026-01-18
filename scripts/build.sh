#!/bin/bash

# 统一打包脚本 - 打包所有微服务
# 打包后的文件统一输出到 dist/ 目录

set -e  # 遇到错误立即退出

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT=$(pwd)
DIST_DIR="$PROJECT_ROOT/dist"

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

# 清理并创建dist目录
print_info "清理并创建 dist 目录..."
rm -rf "$DIST_DIR"
mkdir -p "$DIST_DIR"

# ==================== Spring 服务打包 ====================
build_spring() {
    print_info "开始打包 Spring 服务..."
    cd "$PROJECT_ROOT/spring"
    
    # Maven 打包
    if command -v mvn &> /dev/null; then
        print_info "使用全局 Maven 打包 Spring..."
        mvn clean package -DskipTests
    elif [ -f "./mvnw" ]; then
        print_info "使用本地 Maven Wrapper 打包 Spring..."
        ./mvnw clean package -DskipTests
    else
        print_error "Maven 未安装，跳过 Spring 打包"
        return 1
    fi
    
    # 创建发布目录
    SPRING_DIST="$DIST_DIR/spring"
    mkdir -p "$SPRING_DIST"
    
    # 复制 jar 文件
    cp target/spring-*.jar "$SPRING_DIST/spring.jar"
    
    # 复制配置文件
    cp -r src/main/resources/* "$SPRING_DIST/"
    
    # 复制 .env 文件
    if [ -f ".env" ]; then
        cp .env "$SPRING_DIST/"
    fi
    
    # 创建启动脚本
    cat > "$SPRING_DIST/start.sh" << 'EOF'
#!/bin/bash
JAVA_OPTS="-Xms512m -Xmx1024m"
LOG_DIR="../logs/spring"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/app_$(date +%Y-%m-%d).log"

# 加载 .env 文件并导出到环境变量
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# 将环境变量转换为 Java 系统属性
for var in $(cat .env | grep -v '^#' | cut -d= -f1); do
    JAVA_OPTS="$JAVA_OPTS -D$var=${!var}"
done

nohup java $JAVA_OPTS -jar spring.jar --spring.config.location=bootstrap.yaml,application.yaml >> "$LOG_FILE" 2>&1 &
echo $! > spring.pid
echo "Spring 服务已启动，PID: $(cat spring.pid)"
EOF
    
    cat > "$SPRING_DIST/stop.sh" << 'EOF'
#!/bin/bash
if [ -f spring.pid ]; then
    kill $(cat spring.pid)
    rm spring.pid
    echo "Spring 服务已停止"
else
    echo "未找到 PID 文件"
fi
EOF
    
    chmod +x "$SPRING_DIST/start.sh"
    chmod +x "$SPRING_DIST/stop.sh"
    
    print_info "Spring 服务打包完成: $SPRING_DIST"
}

# ==================== Gateway 服务打包 ====================
build_gateway() {
    print_info "开始打包 Gateway 服务..."
    cd "$PROJECT_ROOT/gateway"
    
    # Maven 打包
    if command -v mvn &> /dev/null; then
        print_info "使用全局 Maven 打包 Gateway..."
        mvn clean package -DskipTests
    elif [ -f "./mvnw" ]; then
        print_info "使用本地 Maven Wrapper 打包 Gateway..."
        ./mvnw clean package -DskipTests
    else
        print_error "Maven 未安装，跳过 Gateway 打包"
        return 1
    fi
    
    # 创建发布目录
    GATEWAY_DIST="$DIST_DIR/gateway"
    mkdir -p "$GATEWAY_DIST"
    
    # 复制 jar 文件
    cp target/gateway-*.jar "$GATEWAY_DIST/gateway.jar"
    
    # 复制配置文件
    cp -r src/main/resources/* "$GATEWAY_DIST/"
    
    # 复制 .env 文件
    if [ -f ".env" ]; then
        cp .env "$GATEWAY_DIST/"
    fi
    
    # 创建启动脚本
    cat > "$GATEWAY_DIST/start.sh" << 'EOF'
#!/bin/bash
JAVA_OPTS="-Xms512m -Xmx1024m"
LOG_DIR="../logs/gateway"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/app_$(date +%Y-%m-%d).log"

# 加载 .env 文件并导出到环境变量
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# 将环境变量转换为 Java 系统属性
for var in $(cat .env | grep -v '^#' | cut -d= -f1); do
    JAVA_OPTS="$JAVA_OPTS -D$var=${!var}"
done

nohup java $JAVA_OPTS -jar gateway.jar --spring.config.location=application.yaml >> "$LOG_FILE" 2>&1 &
echo $! > gateway.pid
echo "Gateway 服务已启动，PID: $(cat gateway.pid)"
EOF
    
    cat > "$GATEWAY_DIST/stop.sh" << 'EOF'
#!/bin/bash
if [ -f gateway.pid ]; then
    kill $(cat gateway.pid)
    rm gateway.pid
    echo "Gateway 服务已停止"
else
    echo "未找到 PID 文件"
fi
EOF
    
    chmod +x "$GATEWAY_DIST/start.sh"
    chmod +x "$GATEWAY_DIST/stop.sh"
    
    print_info "Gateway 服务打包完成: $GATEWAY_DIST"
}

# ==================== FastAPI 服务打包 ====================
build_fastapi() {
    print_info "开始打包 FastAPI 服务..."
    cd "$PROJECT_ROOT/fastapi"
    
    # 创建发布目录
    FASTAPI_DIST="$DIST_DIR/fastapi"
    mkdir -p "$FASTAPI_DIST"
    
    # 复制源代码
    cp -r api common config entity "$FASTAPI_DIST/"
    cp main.py "$FASTAPI_DIST/"
    
    # 复制配置文件
    cp application.yaml "$FASTAPI_DIST/"
    
    # 复制 .env 文件
    if [ -f ".env" ]; then
        cp .env "$FASTAPI_DIST/"
    fi
    
    # 复制 uv 配置文件
    cp pyproject.toml "$FASTAPI_DIST/"
    if [ -f uv.lock ]; then
        cp uv.lock "$FASTAPI_DIST/"
    fi
    
    # 检查是否存在 .venv 虚拟环境
    if [ -d ".venv" ]; then
        print_info "检测到开发环境中存在 .venv 虚拟环境，进行打包..."
        cp -r .venv "$FASTAPI_DIST/"
        
        # 创建启动脚本 - 使用打包后的虚拟环境
        cat > "$FASTAPI_DIST/start.sh" << 'EOF'
#!/bin/bash
LOG_DIR="../logs/fastapi"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/app_$(date +%Y-%m-%d).log"

# 加载 .env 文件
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# 激活虚拟环境
source .venv/bin/activate

# 启动服务
nohup python main.py >> "$LOG_FILE" 2>&1 &
echo $! > fastapi.pid
echo "FastAPI 服务已启动，PID: $(cat fastapi.pid)"
EOF
    else
        print_info "未检测到 .venv 虚拟环境，使用 uv 方式部署..."
        
        # 创建启动脚本 - 使用 uv 同步依赖
        cat > "$FASTAPI_DIST/start.sh" << 'EOF'
#!/bin/bash
LOG_DIR="../logs/fastapi"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/app_$(date +%Y-%m-%d).log"

# 加载 .env 文件
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# 检查 uv 是否已安装
if ! command -v uv &> /dev/null; then
    echo "安装 uv 包管理工具..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
fi

# 同步依赖（如果存在 uv.lock）
if [ -f "uv.lock" ]; then
    echo "使用 uv sync 同步依赖..."
    uv sync
fi

# 启动服务
nohup uv run python main.py >> "$LOG_FILE" 2>&1 &
echo $! > fastapi.pid
echo "FastAPI 服务已启动，PID: $(cat fastapi.pid)"
EOF
    fi
    
    cat > "$FASTAPI_DIST/stop.sh" << 'EOF'
#!/bin/bash
if [ -f fastapi.pid ]; then
    kill $(cat fastapi.pid)
    rm fastapi.pid
    echo "FastAPI 服务已停止"
else
    echo "未找到 PID 文件"
fi
EOF
    
    chmod +x "$FASTAPI_DIST/start.sh"
    chmod +x "$FASTAPI_DIST/stop.sh"
    
    print_info "FastAPI 服务打包完成: $FASTAPI_DIST"
}

# ==================== Gin 服务打包 ====================
build_gin() {
    print_info "开始打包 Gin 服务..."
    cd "$PROJECT_ROOT/gin"
    
    # Go 编译
    if command -v go &> /dev/null; then
        print_info "使用 Go 编译 Gin 服务..."
        go build -o gin_service main.go
    else
        print_error "Go 未安装，跳过 Gin 打包"
        return 1
    fi
    
    # 创建发布目录
    GIN_DIST="$DIST_DIR/gin"
    mkdir -p "$GIN_DIST"
    
    # 复制二进制文件
    # 复制配置文件
    cp application.yaml "$GIN_DIST/"
    
    # 复制 .env 文件
    if [ -f ".env" ]; then
        cp .env "$GIN_DIST/"
    fi
    
    # 创建启动脚本cation.yaml "$GIN_DIST/"
    
    # 创建启动脚本
    cat > "$GIN_DIST/start.sh" << 'EOF'
#!/bin/bash
LOG_DIR="../logs/gin"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/app_$(date +%Y-%m-%d).log"

# 加载 .env 文件
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

nohup ./gin_service >> "$LOG_FILE" 2>&1 &
echo $! > gin.pid
echo "Gin 服务已启动，PID: $(cat gin.pid)"
EOF
    
    cat > "$GIN_DIST/stop.sh" << 'EOF'
#!/bin/bash
if [ -f gin.pid ]; then
    kill $(cat gin.pid)
    rm gin.pid
    echo "Gin 服务已停止"
else
    echo "未找到 PID 文件"
fi
EOF
    
    chmod +x "$GIN_DIST/start.sh"
    chmod +x "$GIN_DIST/stop.sh"
    chmod +x "$GIN_DIST/gin_service"
    
    print_info "Gin 服务打包完成: $GIN_DIST"
}

# ==================== NestJS 服务打包 ====================
build_nestjs() {
    print_info "开始打包 NestJS 服务..."
    cd "$PROJECT_ROOT/nestjs"
    
    # 检查是否使用 bun
    if command -v bun &> /dev/null; then
        print_info "检测到 bun，使用 bun 构建 NestJS..."
        bun install
        bun run build:bun
    elif command -v npm &> /dev/null; then
        print_info "使用 npm 构建 NestJS..."
        npm install
        npm run build
    else
        print_error "npm 和 bun 都未安装，跳过 NestJS 打包"
        return 1
    fi
    
    # 创建发布目录
    NESTJS_DIST="$DIST_DIR/nestjs"
    mkdir -p "$NESTJS_DIST"
    
    # 复制编译后的文件
    cp -r dist "$NESTJS_DIST/"
    
    # 根据使用的包管理器复制依赖
    if command -v bun &> /dev/null; then
        print_info "使用 bun 的依赖..."
        cp -r node_modules "$NESTJS_DIST/"
        cp bunfig.toml "$NESTJS_DIST/" 2>/dev/null || true
    # 复制配置文件
    cp application.yaml "$NESTJS_DIST/"
    cp package.json "$NESTJS_DIST/"
    
    # 复制 .env 文件
    if [ -f ".env" ]; then
        cp .env "$NESTJS_DIST/"
    fi
    
    # 创建启动脚本 - 优先使用 bun
    # 复制配置文件
    cp application.yaml "$NESTJS_DIST/"
    cp package.json "$NESTJS_DIST/"
    
    # 创建启动脚本 - 优先使用 bun
    if command -v bun &> /dev/null; then
        cat > "$NESTJS_DIST/start.sh" << 'EOF'
#!/bin/bash
LOG_DIR="../logs/nestjs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/app_$(date +%Y-%m-%d).log"

# 加载 .env 文件
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# 优先使用 bun 启动
if command -v bun &> /dev/null; then
    nohup bun run dist/main.js >> "$LOG_FILE" 2>&1 &
else
    nohup node dist/main.js >> "$LOG_FILE" 2>&1 &
fi

echo $! > nestjs.pid
echo "NestJS 服务已启动，PID: $(cat nestjs.pid)"
EOF
    else
        cat > "$NESTJS_DIST/start.sh" << 'EOF'
#!/bin/bash
LOG_DIR="../logs/nestjs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/app_$(date +%Y-%m-%d).log"

# 加载 .env 文件
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

nohup node dist/main.js >> "$LOG_FILE" 2>&1 &
echo $! > nestjs.pid
echo "NestJS 服务已启动，PID: $(cat nestjs.pid)"
EOF
    fi
    
    cat > "$NESTJS_DIST/stop.sh" << 'EOF'
#!/bin/bash
if [ -f nestjs.pid ]; then
    kill $(cat nestjs.pid)
    rm nestjs.pid
    echo "NestJS 服务已停止"
else
    echo "未找到 PID 文件"
fi
EOF
    
    chmod +x "$NESTJS_DIST/start.sh"
    chmod +x "$NESTJS_DIST/stop.sh"
    
    print_info "NestJS 服务打包完成: $NESTJS_DIST"
}

# ==================== 主函数 ====================
main() {
    print_info "=========================================="
    print_info "开始统一打包所有微服务"
    print_info "=========================================="
    
    # 解析参数
    SERVICES=()
    if [ $# -eq 0 ]; then
        # 默认打包所有服务
        SERVICES=("spring" "gateway" "fastapi" "gin" "nestjs")
    else
        SERVICES=("$@")
    fi
    
    # 打包各个服务
    for service in "${SERVICES[@]}"; do
        case "$service" in
            spring)
                build_spring || print_warn "Spring 打包失败"
                ;;
            gateway)
                build_gateway || print_warn "Gateway 打包失败"
                ;;
            fastapi)
                build_fastapi || print_warn "FastAPI 打包失败"
                ;;
            gin)
                build_gin || print_warn "Gin 打包失败"
                ;;
            nestjs)
                build_nestjs || print_warn "NestJS 打包失败"
                ;;
            *)
                print_error "未知服务: $service"
                ;;
        esac
        echo ""
    done
    
    # 复制 static 目录
    print_info "复制 static 目录到 dist..."
    if [ -d "$PROJECT_ROOT/static" ]; then
        cp -r "$PROJECT_ROOT/static" "$DIST_DIR/"
        print_info "static 目录已复制到 $DIST_DIR/static"
    else
        print_warn "static 目录不存在，跳过复制"
    fi
    
    print_info "=========================================="
    print_info "打包完成！所有文件位于: $DIST_DIR"
    print_info "=========================================="
    
    # 显示目录结构
    if command -v tree &> /dev/null; then
        tree -L 2 "$DIST_DIR"
    else
        ls -lh "$DIST_DIR"
    fi
}

# 执行主函数
main "$@"

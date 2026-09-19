#!/bin/bash

# 统一打包脚本 - 打包所有微服务
# 打包后的文件统一输出到 dist/ 目录

set -e  # 遇到错误立即退出

# 加载环境变量
if [ -f ".env" ]; then
    set -a
    . ./.env
    set +a
fi

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

# ==================== 强制清理（Docker 兜底） ====================
# 容器写入宿主机挂载目录后，文件属主是容器内的用户，与当前登录用户不一致：
#   - gateway(APISIX) 以 uid 636 写入 dist/logs/gateway，其它服务若以 root 运行同理
#   - 切回常规打包（dist build）时，rm -rf 无权删除，配合 set -e 会直接中断
# 因此清理分两级：先尝试普通 rm，仍有残留时用一次性 root 容器删除
FORCE_CLEAN_IMAGE="${FORCE_CLEAN_IMAGE:-alpine:3.20}"

# 使用 root 容器删除项目根目录下的相对路径（挂在 /work 上删除子路径，可连同目录本身一起删除）
docker_force_remove() {
    local rel_paths=("$@")
    local targets=()
    local rel

    command -v docker >/dev/null 2>&1 || return 1
    if ! docker image inspect "$FORCE_CLEAN_IMAGE" >/dev/null 2>&1; then
        docker pull "$FORCE_CLEAN_IMAGE" >/dev/null 2>&1 || return 1
    fi

    for rel in "${rel_paths[@]}"; do
        targets+=("/work/$rel")
    done

    docker run --rm -v "$PROJECT_ROOT:/work" "$FORCE_CLEAN_IMAGE" \
        rm -rf -- "${targets[@]}" >/dev/null 2>&1
}

# 删除项目根目录下的相对路径；返回 0 表示已清理干净，返回 1 表示仍有残留
force_remove_project_paths() {
    local rel_paths=("$@")
    local existing=()
    local rm_targets=()
    local leftovers=()
    local rel

    for rel in "${rel_paths[@]}"; do
        if [ -e "$PROJECT_ROOT/$rel" ]; then
            existing+=("$rel")
        fi
    done
    if [ ${#existing[@]} -eq 0 ]; then
        return 0
    fi

    for rel in "${existing[@]}"; do
        rm_targets+=("$PROJECT_ROOT/$rel")
    done
    rm -rf -- "${rm_targets[@]}" 2>/dev/null || true

    for rel in "${existing[@]}"; do
        if [ -e "$PROJECT_ROOT/$rel" ]; then
            leftovers+=("$rel")
        fi
    done
    if [ ${#leftovers[@]} -eq 0 ]; then
        return 0
    fi

    print_warn "检测到容器写入的非当前用户属主文件，改用 Docker 强制清理: ${leftovers[*]}"
    docker_force_remove "${leftovers[@]}" || return 1

    for rel in "${leftovers[@]}"; do
        if [ -e "$PROJECT_ROOT/$rel" ]; then
            return 1
        fi
    done
    return 0
}

# 清理并创建dist目录
# dist/logs/<service> 可能由容器（APISIX uid 636、其他镜像 root）写入并保留在 dist 下，
# 普通 rm 无权删除，这里统一走 Docker 兜底，避免 set -e 中断打包
print_info "清理并创建 dist 目录..."
if [ -d "$DIST_DIR" ]; then
    if ! force_remove_project_paths "dist"; then
        print_error "dist 目录未能完全清理（残留文件属主非当前用户，且 Docker 不可用或清理失败）"
        print_error "请手动执行: sudo rm -rf \"$DIST_DIR\""
    fi
fi
mkdir -p "$DIST_DIR"

# ==================== Spring 服务打包 ====================
build_spring() {
    print_info "开始打包 Spring 服务..."
    OTEL_ENABLED=true bash "$PROJECT_ROOT/scripts/otel-env.sh" spring
    cd "$PROJECT_ROOT/spring"
    
    # Gradle 打包
    if command -v gradle &> /dev/null; then
        print_info "使用全局 Gradle 打包 Spring..."
        gradle clean build -x test
    elif [ -f "./gradlew" ]; then
        print_info "使用本地 Gradle Wrapper 打包 Spring..."
        ./gradlew clean build -x test
    else
        print_error "Gradle 未安装，跳过 Spring 打包"
        return 1
    fi
    
    # 创建发布目录
    SPRING_DIST="$DIST_DIR/spring"
    mkdir -p "$SPRING_DIST"
    
    # 复制 jar 文件（排除 plain jar，只复制可执行的 jar）
    if [ -f "build/libs/spring-1.0.0.jar" ]; then
        cp "build/libs/spring-1.0.0.jar" "$SPRING_DIST/spring.jar"
    elif ls build/libs/spring-*.jar 1> /dev/null 2>&1; then
        # 如果上面的文件不存在，使用通配符找到第一个 jar 文件
        cp $(ls build/libs/spring-*.jar | grep -v plain | head -1) "$SPRING_DIST/spring.jar"
    else
        print_error "未找到 Spring jar 文件"
        return 1
    fi
    
    # 复制配置文件
    if [ -d "src/main/resources" ]; then
        cp -r src/main/resources/* "$SPRING_DIST/"
    fi
    
    # 复制 .env 文件
    if [ -f ".env" ]; then
        cp .env "$SPRING_DIST/"
    fi
    cp "$PROJECT_ROOT/.otel/opentelemetry-javaagent.jar" "$SPRING_DIST/"
    
    # 创建启动脚本
    cat > "$SPRING_DIST/start.sh" << 'EOF'
#!/bin/bash
JAVA_OPTS="-Xms512m -Xmx1024m"
LOG_DIR="../logs/spring"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/app_$(date +%Y-%m-%d).log"

# 加载 .env 文件
if [ -f ".env" ]; then
    set -a
    . ./.env
    set +a
fi

if [ -z "${OTEL_ENABLED+x}" ]; then
    [ -f "../../.otel/enabled" ] && export OTEL_ENABLED=true || export OTEL_ENABLED=false
fi
export OTEL_SERVICE_NAME="${OTEL_SERVICE_NAME:-spring}"
export OTEL_EXPORTER_OTLP_ENDPOINT="${OTEL_EXPORTER_OTLP_ENDPOINT:-http://127.0.0.1:4318}"
export OTEL_EXPORTER_OTLP_PROTOCOL="${OTEL_EXPORTER_OTLP_PROTOCOL:-http/protobuf}"
export OTEL_TRACES_SAMPLER="${OTEL_TRACES_SAMPLER:-always_on}"
if [ "$OTEL_ENABLED" = "true" ]; then
    JAVA_OPTS="$JAVA_OPTS -javaagent:$(pwd)/opentelemetry-javaagent.jar"
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
    print_info "开始打包 Gateway 服务(APISIX)..."
    cd "$PROJECT_ROOT/gateway"

    if [ ! -f "apisix/config.yaml" ] || [ ! -f "apisix/apisix.yaml" ]; then
        print_error "缺少 APISIX 配置文件"
        return 1
    fi

    GATEWAY_DIST="$DIST_DIR/gateway"
    mkdir -p "$GATEWAY_DIST"

    cp -r apisix swagger-ui "$GATEWAY_DIST/"
    cp docker-compose.yml "$GATEWAY_DIST/"

    cat > "$GATEWAY_DIST/start.sh" << 'EOF'
#!/bin/bash
set -e
cd "$(dirname "$0")"
mkdir -p ../logs/gateway
if [ -z "${APISIX_OTEL_ENABLED+x}" ]; then
    [ -f "../../.otel/enabled" ] && export APISIX_OTEL_ENABLED=true || export APISIX_OTEL_ENABLED=false
fi
if docker ps -a --format '{{.Names}}' | grep -qx mix-gateway; then
    docker rm -f mix-gateway >/dev/null
fi
docker compose down --remove-orphans >/dev/null 2>&1 || true
docker compose up -d
EOF

    cat > "$GATEWAY_DIST/stop.sh" << 'EOF'
#!/bin/bash
set -e
cd "$(dirname "$0")"
docker compose down
EOF

    chmod +x "$GATEWAY_DIST/start.sh"
    chmod +x "$GATEWAY_DIST/stop.sh"

    print_info "Gateway 服务打包完成: $GATEWAY_DIST"
}

# ==================== FastAPI 服务打包 ====================
build_fastapi() {
    print_info "开始打包 FastAPI 服务..."
    cd "$PROJECT_ROOT/fastapi"

    if command -v uv &> /dev/null; then
        uv sync --frozen
    elif [ -x ".venv/bin/pip" ]; then
        .venv/bin/pip install -r requirements.txt
    else
        print_error "未找到 uv 或可用的 FastAPI 虚拟环境"
        return 1
    fi
    
    # 创建发布目录
    FASTAPI_DIST="$DIST_DIR/fastapi"
    mkdir -p "$FASTAPI_DIST"
    
    # 复制源代码
    cp -r app "$FASTAPI_DIST/"
    cp main.py "$FASTAPI_DIST/"
    
    # 复制配置文件
    cp application.yaml "$FASTAPI_DIST/"
    cp requirements.txt "$FASTAPI_DIST/"
    
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
        
        # 创建启动脚本 - 使用虚拟环境
        cat > "$FASTAPI_DIST/start.sh" << 'EOF'
#!/bin/bash
LOG_DIR="../logs/fastapi"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/app_$(date +%Y-%m-%d).log"

# 加载 .env 文件
if [ -f ".env" ]; then
    set -a
    . ./.env
    set +a
fi

if [ -z "${OTEL_ENABLED+x}" ]; then
    [ -f "../../.otel/enabled" ] && export OTEL_ENABLED=true || export OTEL_ENABLED=false
fi
export OTEL_SERVICE_NAME="${OTEL_SERVICE_NAME:-fastapi}"
export OTEL_EXPORTER_OTLP_ENDPOINT="${OTEL_EXPORTER_OTLP_ENDPOINT:-http://127.0.0.1:4318}"
export OTEL_EXPORTER_OTLP_TRACES_ENDPOINT="${OTEL_EXPORTER_OTLP_TRACES_ENDPOINT:-${OTEL_EXPORTER_OTLP_ENDPOINT%/}/v1/traces}"
export OTEL_TRACES_SAMPLER="${OTEL_TRACES_SAMPLER:-always_on}"

# 激活虚拟环境
source .venv/bin/activate

# 启动服务
nohup python main.py >> "$LOG_FILE" 2>&1 &
echo $! > fastapi.pid
echo "FastAPI 服务已启动，PID: $(cat fastapi.pid)"
EOF
    else
        print_info "未检测到 .venv 虚拟环境，使用灵活启动方式..."
        
        # 创建启动脚本 - 使用虚拟环境
        cat > "$FASTAPI_DIST/start.sh" << 'EOF'
#!/bin/bash
LOG_DIR="../logs/fastapi"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/app_$(date +%Y-%m-%d).log"

# 加载 .env 文件
if [ -f ".env" ]; then
    set -a
    . ./.env
    set +a
fi

if [ -z "${OTEL_ENABLED+x}" ]; then
    [ -f "../../.otel/enabled" ] && export OTEL_ENABLED=true || export OTEL_ENABLED=false
fi
export OTEL_SERVICE_NAME="${OTEL_SERVICE_NAME:-fastapi}"
export OTEL_EXPORTER_OTLP_ENDPOINT="${OTEL_EXPORTER_OTLP_ENDPOINT:-http://127.0.0.1:4318}"
export OTEL_EXPORTER_OTLP_TRACES_ENDPOINT="${OTEL_EXPORTER_OTLP_TRACES_ENDPOINT:-${OTEL_EXPORTER_OTLP_ENDPOINT%/}/v1/traces}"
export OTEL_TRACES_SAMPLER="${OTEL_TRACES_SAMPLER:-always_on}"

# 激活虚拟环境
source .venv/bin/activate

# 启动服务
nohup python main.py >> "$LOG_FILE" 2>&1 &
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

# ==================== GoZero 服务打包 ====================
build_gozero() {
    print_info "开始打包 GoZero 服务..."
    cd "$PROJECT_ROOT/gozero/app"
    
    # Go 编译
    if command -v go &> /dev/null; then
        print_info "使用 Go 编译 GoZero 服务..."
        go build -o gozero main.go
        
        if [ $? -ne 0 ]; then
            print_error "GoZero 编译失败"
            return 1
        fi
    else
        print_error "Go 未安装，跳过 GoZero 打包"
        return 1
    fi
    
    # 创建发布目录
    GOZERO_DIST="$DIST_DIR/gozero"
    mkdir -p "$GOZERO_DIST"
    
    # 复制二进制文件
    cp gozero "$GOZERO_DIST/"
    
    # 复制配置文件（保留 etc/ 目录结构，与二进制默认路径一致）
    mkdir -p "$GOZERO_DIST/etc"
    cp etc/application.yaml "$GOZERO_DIST/etc/"
    
    # 复制 Swagger 文档（运行时通过相对路径 docs/main.json 读取）
    cp -r docs "$GOZERO_DIST/"
    
    # 复制 .env 文件
    if [ -f ".env" ]; then
        cp .env "$GOZERO_DIST/"
    fi
    
    # 创建启动脚本
    cat > "$GOZERO_DIST/start.sh" << 'EOF'
#!/bin/bash
LOG_DIR="../logs/gozero"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/app_$(date +%Y-%m-%d).log"

# 加载 .env 文件
if [ -f ".env" ]; then
    set -a
    . ./.env
    set +a
fi

if [ -z "${OTEL_ENABLED+x}" ]; then
    [ -f "../../.otel/enabled" ] && export OTEL_ENABLED=true || export OTEL_ENABLED=false
fi
export OTEL_DISABLED="$([ "$OTEL_ENABLED" = "true" ] && echo false || echo true)"
export OTEL_SERVICE_NAME="${OTEL_SERVICE_NAME:-gozero}"
export OTEL_EXPORTER_OTLP_ENDPOINT="${OTEL_EXPORTER_OTLP_ENDPOINT:-127.0.0.1:4318}"
export OTEL_TRACES_SAMPLER_RATIO="${OTEL_TRACES_SAMPLER_RATIO:-1.0}"

nohup ./gozero >> "$LOG_FILE" 2>&1 &
echo $! > gozero.pid
echo "GoZero 服务已启动，PID: $(cat gozero.pid)"
EOF
    
    cat > "$GOZERO_DIST/stop.sh" << 'EOF'
#!/bin/bash
if [ -f gozero.pid ]; then
    kill $(cat gozero.pid)
    rm gozero.pid
    echo "GoZero 服务已停止"
else
    echo "未找到 PID 文件"
fi
EOF
    
    chmod +x "$GOZERO_DIST/start.sh"
    chmod +x "$GOZERO_DIST/stop.sh"
    chmod +x "$GOZERO_DIST/gozero"
    
    print_info "GoZero 服务打包完成: $GOZERO_DIST"
}

# ==================== NestJS 服务打包 ====================
build_nestjs() {
    print_info "开始打包 NestJS 服务..."
    cd "$PROJECT_ROOT/nestjs"
    
    # 检查是否使用 bun
    if command -v bun &> /dev/null; then
        print_info "检测到 bun，使用 bun 构建 NestJS..."
        bun install
        bun run bun:build
    elif command -v npm &> /dev/null; then
        print_info "使用 npm 构建 NestJS..."
        npm install
        npm run node:build
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
    else
        print_info "使用 npm 的依赖..."
        cp -r node_modules "$NESTJS_DIST/"
    fi
    
    # 复制配置文件（tsc 不会自动复制非 .ts 文件，application.yaml 需要随 dist/config 一起打包）
    mkdir -p "$NESTJS_DIST/dist/config"
    cp src/config/application.yaml "$NESTJS_DIST/dist/config/application.yaml"
    cp package.json "$NESTJS_DIST/"
    
    # 复制 .env 文件
    if [ -f ".env" ]; then
        cp .env "$NESTJS_DIST/"
    fi
    
    # 创建启动脚本 - 优先使用 bun
    if command -v bun &> /dev/null; then
        cat > "$NESTJS_DIST/start.sh" << 'EOF'
#!/bin/bash
LOG_DIR="../logs/nestjs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/app_$(date +%Y-%m-%d).log"

# 加载 .env 文件
if [ -f ".env" ]; then
    set -a
    . ./.env
    set +a
fi

if [ -z "${OTEL_ENABLED+x}" ]; then
    [ -f "../../.otel/enabled" ] && export OTEL_ENABLED=true || export OTEL_ENABLED=false
fi
export OTEL_SERVICE_NAME="${OTEL_SERVICE_NAME:-nestjs}"
export OTEL_EXPORTER_OTLP_ENDPOINT="${OTEL_EXPORTER_OTLP_ENDPOINT:-http://127.0.0.1:4318}"
export OTEL_EXPORTER_OTLP_TRACES_ENDPOINT="${OTEL_EXPORTER_OTLP_TRACES_ENDPOINT:-${OTEL_EXPORTER_OTLP_ENDPOINT%/}/v1/traces}"
export OTEL_TRACES_SAMPLER="${OTEL_TRACES_SAMPLER:-always_on}"

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
    set -a
    . ./.env
    set +a
fi

if [ -z "${OTEL_ENABLED+x}" ]; then
    [ -f "../../.otel/enabled" ] && export OTEL_ENABLED=true || export OTEL_ENABLED=false
fi
export OTEL_SERVICE_NAME="${OTEL_SERVICE_NAME:-nestjs}"
export OTEL_EXPORTER_OTLP_ENDPOINT="${OTEL_EXPORTER_OTLP_ENDPOINT:-http://127.0.0.1:4318}"
export OTEL_EXPORTER_OTLP_TRACES_ENDPOINT="${OTEL_EXPORTER_OTLP_TRACES_ENDPOINT:-${OTEL_EXPORTER_OTLP_ENDPOINT%/}/v1/traces}"
export OTEL_TRACES_SAMPLER="${OTEL_TRACES_SAMPLER:-always_on}"

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
        SERVICES=("spring" "gateway" "fastapi" "gozero" "nestjs")
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
            gozero)
                build_gozero || print_warn "GoZero 打包失败"
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

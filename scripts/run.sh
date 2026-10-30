#!/bin/bash

SESSION="multi-services"
WORKDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# 默认配置
DEFAULT_JAVA_BUILD="maven"  # gradle 或 maven
DEFAULT_NODE_RUNTIME="bun"   # bun 或 npm
DEFAULT_PYTHON_RUNTIME="uv"  # uv 或 python

# 解析命令行参数
JAVA_BUILD="$DEFAULT_JAVA_BUILD"
NODE_RUNTIME="$DEFAULT_NODE_RUNTIME"
PYTHON_RUNTIME="$DEFAULT_PYTHON_RUNTIME"
INTERACTIVE_MODE=false

# 显示帮助信息
show_help() {
    cat << EOF
使用方法: $0 [选项]

选项:
  -h, --help              显示此帮助信息
  -i, --interactive       进入交互式选择模式
  --java-build TOOL       设置 Java 构建工具 (gradle|maven)，默认: $DEFAULT_JAVA_BUILD
  --node-runtime TOOL     设置 Node.js 运行时 (bun|npm)，默认: $DEFAULT_NODE_RUNTIME
  --python-runtime TOOL   设置 Python 运行时 (uv|python)，默认: $DEFAULT_PYTHON_RUNTIME

示例:
  # 使用默认配置（gradle + bun + uv）
  $0

  # 进入交互式选择模式
  $0 -i
  $0 --interactive

  # 指定具体配置
  $0 --java-build maven --node-runtime npm --python-runtime python

  # 混合使用
  $0 --java-build maven -i
EOF
}

# 解析参数
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -i|--interactive)
            INTERACTIVE_MODE=true
            shift
            ;;
        --java-build)
            JAVA_BUILD="$2"
            shift 2
            ;;
        --node-runtime)
            NODE_RUNTIME="$2"
            shift 2
            ;;
        --python-runtime)
            PYTHON_RUNTIME="$2"
            shift 2
            ;;
        *)
            echo "未知选项: $1"
            show_help
            exit 1
            ;;
    esac
done

# 验证参数
validate_option() {
    local option=$1
    local value=$2
    local valid_values=$3

    if [[ ! "$valid_values" =~ (^|,)$value(,|$) ]]; then
        echo "错误: 无效的 $option 值: $value"
        echo "有效值: $valid_values"
        exit 1
    fi
}

validate_option "java-build" "$JAVA_BUILD" "gradle,maven"
validate_option "node-runtime" "$NODE_RUNTIME" "bun,npm"
validate_option "python-runtime" "$PYTHON_RUNTIME" "uv,python"

# 交互式选择模式
if [ "$INTERACTIVE_MODE" = true ]; then
    echo "======================================="
    echo "    多服务启动 - 交互式配置选择"
    echo "======================================="
    echo ""

    # Java 构建工具选择
    echo "【1】请选择 Java 构建工具 (Spring):"
    echo "    1) gradle"
    echo "    2) maven (默认)"
    read -p "请输入选择 [2]: " java_choice
    java_choice=${java_choice:-2}
    case $java_choice in
        1) JAVA_BUILD="gradle" ;;
        2) JAVA_BUILD="maven" ;;
        *) echo "无效选择，使用默认值: maven"; JAVA_BUILD="maven" ;;
    esac

    echo ""

    # Node.js 运行时选择
    echo "【2】请选择 Node.js 运行时 (NestJS):"
    echo "    1) bun (推荐，更快) [默认]"
    echo "    2) npm"
    read -p "请输入选择 [1]: " node_choice
    node_choice=${node_choice:-1}
    case $node_choice in
        1) NODE_RUNTIME="bun" ;;
        2) NODE_RUNTIME="npm" ;;
        *) echo "无效选择，使用默认值: bun"; NODE_RUNTIME="bun" ;;
    esac

    echo ""

    # Python 运行时选择
    echo "【3】请选择 Python 运行时 (FastAPI):"
    echo "    1) uv (推荐，更快) [默认]"
    echo "    2) python (原生)"
    read -p "请输入选择 [1]: " python_choice
    python_choice=${python_choice:-1}
    case $python_choice in
        1) PYTHON_RUNTIME="uv" ;;
        2) PYTHON_RUNTIME="python" ;;
        *) echo "无效选择，使用默认值: uv"; PYTHON_RUNTIME="uv" ;;
    esac

    echo ""
fi

# 显示启动配置
echo "======================================="
echo "    启动配置信息"
echo "======================================="
echo "Java 构建工具:        $JAVA_BUILD"
echo "Node.js 运行时:       $NODE_RUNTIME"
echo "Python 运行时:        $PYTHON_RUNTIME"
echo "======================================="
echo ""

# 构造 Java 启动命令
if [ "$JAVA_BUILD" = "gradle" ]; then
    java_cmd="gradle bootRun --continuous"
else
    java_cmd="mvn spring-boot:run"
fi

# 构造 Node.js 启动命令
if [ "$NODE_RUNTIME" = "bun" ]; then
    node_cmd="npm run bun:dev"
else
    node_cmd="npm run node:start:dev"
fi

# 构造 Python 启动命令
if [ "$PYTHON_RUNTIME" = "uv" ]; then
    python_cmd="uv run python main.py"
else
    python_cmd="source .venv/bin/activate && python main.py"
fi

# 创建会话并设置第一个窗口为 spring（编号 1）
tmux new-session -d -s $SESSION -n spring -c "$WORKDIR"
tmux move-window -s $SESSION:0 -t $SESSION:1
tmux send-keys -t $SESSION:1 \
"cd spring && if [ -f .env ]; then set -a && . ./.env && set +a; fi && source '$WORKDIR/scripts/otel-env.sh' spring && $java_cmd" C-m

# window 2: gozero
tmux new-window -t $SESSION:2 -n gozero -c "$WORKDIR"
tmux send-keys -t $SESSION:2 \
"cd gozero/app && if [ -f .env ]; then set -a && . ./.env && set +a; fi && source '$WORKDIR/scripts/otel-env.sh' gozero && fresh" C-m

# window 3: nestjs
tmux new-window -t $SESSION:3 -n nestjs -c "$WORKDIR"
tmux send-keys -t $SESSION:3 \
"cd nestjs && if [ -f .env ]; then set -a && . ./.env && set +a; fi && source '$WORKDIR/scripts/otel-env.sh' nestjs && $node_cmd" C-m

# window 4: fastapi
tmux new-window -t $SESSION:4 -n fastapi -c "$WORKDIR"
tmux send-keys -t $SESSION:4 \
"cd fastapi && if [ -f .env ]; then set -a && . ./.env && set +a; fi && source '$WORKDIR/scripts/otel-env.sh' fastapi && $python_cmd" C-m

# window 5: gateway
# 先清理残留网关容器，dev 模式（gateway/docker-compose.yml）与根 compose 共用
# container_name: mix-gateway，若之前通过 ./mix compose up 启动过会报容器名冲突
bash "$WORKDIR/scripts/gateway-cleanup.sh"

# 等待四个服务在 Nacos 注册完成后再拉起网关
# 网关的 Nacos 发现只在启动时拉取一次服务列表、之后只刷新已知服务，
# 若此刻服务尚未注册，上游节点会一直是空：/swagger/*.json 返回 503，
# error.log 里是 "no valid upstream node: nil"。超时只告警不阻断启动
wait_nacos_registration() {
    local nacos="${NACOS_ADDR:-127.0.0.1:8848}"
    local timeout="${1:-120}"
    local deadline=$((SECONDS + timeout))
    local pending="" service

    if ! command -v curl >/dev/null 2>&1; then
        echo "未找到 curl，跳过 Nacos 注册等待"
        return 0
    fi

    while [ $SECONDS -lt $deadline ]; do
        pending=""
        for service in spring gozero nestjs fastapi; do
            if ! curl -s --noproxy '*' --max-time 2 \
                "http://$nacos/nacos/v1/ns/instance/list?serviceName=$service" 2>/dev/null |
                grep -q '"hosts":\[{'; then
                pending="$pending $service"
            fi
        done
        if [ -z "$pending" ]; then
            echo "四个服务已在 Nacos 注册，开始启动网关"
            return 0
        fi
        sleep 3
    done

    echo "警告：以下服务在 ${timeout}s 内未完成 Nacos 注册:$pending"
    echo "      网关可能返回 503；服务就绪后可重建网关: cd gateway && docker compose up -d --force-recreate"
    return 0
}

wait_nacos_registration 120

# docker compose v2.35.x 并发拉取镜像会崩（docker/compose#12747），先串行预拉一遍，
# 镜像命中本地缓存后 compose up 不再走并发拉取分支；拉取失败不阻断，交给 compose 处理
bash "$WORKDIR/scripts/prepull-images.sh" "$WORKDIR/gateway/docker-compose.yml" "docker compose"

tmux new-window -t $SESSION:5 -n gateway -c "$WORKDIR"
tmux send-keys -t $SESSION:5 \
"source '$WORKDIR/scripts/otel-env.sh' gateway && echo 'Starting APISIX Gateway...' && bash '$WORKDIR/scripts/gateway-dev.sh'" C-m

# 选择 spring 窗口并附加
tmux select-window -t $SESSION:1
tmux attach -t $SESSION

#!/bin/bash

SESSION="multi-services"
WORKDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# 默认配置
DEFAULT_JAVA_BUILD="gradle"  # gradle 或 maven
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
    echo "【1】请选择 Java 构建工具 (Spring & Gateway):"
    echo "    1) gradle (推荐，更快) [默认]"
    echo "    2) maven"
    read -p "请输入选择 [1]: " java_choice
    java_choice=${java_choice:-1}
    case $java_choice in
        1) JAVA_BUILD="gradle" ;;
        2) JAVA_BUILD="maven" ;;
        *) echo "无效选择，使用默认值: gradle"; JAVA_BUILD="gradle" ;;
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
    java_cmd="gradle bootRun"
else
    java_cmd="mvn spring-boot:run"
fi

# 构造 Node.js 启动命令
if [ "$NODE_RUNTIME" = "bun" ]; then
    node_cmd="npm run bun:dev"
else
    node_cmd="npm run start:dev"
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
"cd spring && [ -f .env ] && export \$(cat .env | grep -v '^#' | xargs) && $java_cmd" C-m

# window 2: gin
tmux new-window -t $SESSION:2 -n gin -c "$WORKDIR"
tmux send-keys -t $SESSION:2 \
"cd gin && [ -f .env ] && export \$(cat .env | grep -v '^#' | xargs) && fresh -c ~/.freshrc" C-m

# window 3: nestjs
tmux new-window -t $SESSION:3 -n nestjs -c "$WORKDIR"
tmux send-keys -t $SESSION:3 \
"cd nestjs && [ -f .env ] && export \$(cat .env | grep -v '^#' | xargs) && $node_cmd" C-m

# window 4: fastapi
tmux new-window -t $SESSION:4 -n fastapi -c "$WORKDIR"
tmux send-keys -t $SESSION:4 \
"cd fastapi && [ -f .env ] && export \$(cat .env | grep -v '^#' | xargs) && $python_cmd" C-m

# window 5: gateway
tmux new-window -t $SESSION:5 -n gateway -c "$WORKDIR"
tmux send-keys -t $SESSION:5 \
"cd gateway && [ -f .env ] && export \$(cat .env | grep -v '^#' | xargs) && $java_cmd" C-m

# 选择 spring 窗口并附加
tmux select-window -t $SESSION:1
tmux attach -t $SESSION

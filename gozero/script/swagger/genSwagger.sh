#!/bin/bash
# 生成 GoZero 的 Swagger/OpenAPI 文档 - 使用 goctl 从 .api 生成
#
# 流程：
#   1. goctl 从 main.api 生成 main.json（goctl 的输出名取自 --api 的文件名）
#   2. 按仓库约定改名为 openapi.json
#   3. swagger2openapi 转换为 OpenAPI 3.0（fix.py 的处理都按 3.0 结构编写，必需；未安装则自动安装）
#   4. fix.py 补中文标签、剔除易变字段与 WebSocket 路径，并由处理后的 JSON 派生 openapi.yaml
#
# YAML 不由 goctl 单独生成：那样会停留在 Swagger 2.0，与已是 OpenAPI 3 的 JSON 格式分叉

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
GOZERO_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
API_DIR="$GOZERO_DIR/api"
DOCS_DIR="$GOZERO_DIR/app/docs"
JSON_FILE="$DOCS_DIR/openapi.json"
YAML_FILE="$DOCS_DIR/openapi.yaml"

echo "正在验证goctl工具..."
if ! command -v goctl &> /dev/null
then
    echo "错误: goctl未安装"
    echo "请先安装goctl: go install github.com/zeromicro/go-zero/tools/goctl@latest"
    exit 1
fi

# 创建输出目录
mkdir -p "$DOCS_DIR"

# 进入api目录
cd "$API_DIR" || exit 1

echo "正在生成Swagger文档..."
goctl api swagger --api main.api --dir "$DOCS_DIR"

# goctl 固定输出 main.json，这里按本仓库约定改名
if [ -f "$DOCS_DIR/main.json" ]; then
    mv -f "$DOCS_DIR/main.json" "$JSON_FILE"
fi

# 清理历史遗留的 main.yaml，避免与派生产物混淆
rm -f "$DOCS_DIR/main.yaml"

if [ ! -f "$JSON_FILE" ]; then
    echo "Swagger文档生成失败"
    exit 1
fi
echo "goctl 生成完成：$JSON_FILE"

# 转换为 OpenAPI 3.0 JSON 格式，直接覆盖 openapi.json
# 未安装时自动安装；装完仍不在当前 PATH 时退化为 npx 调用
s2o=()
if command -v swagger2openapi &> /dev/null; then
    s2o=(swagger2openapi)
else
    echo "未检测到 swagger2openapi，正在自动安装..."
    if ! command -v npm &> /dev/null; then
        echo "错误: 自动安装需要 npm，请先安装 Node.js（自带 npm）后重试"
        exit 1
    fi
    if ! npm install -g swagger2openapi; then
        echo "错误: swagger2openapi 安装失败，请手动执行: npm install -g swagger2openapi"
        exit 1
    fi
    if command -v swagger2openapi &> /dev/null; then
        s2o=(swagger2openapi)
    else
        echo "提示: 全局 bin 目录不在当前 PATH，改用 npx 调用"
        s2o=(npx -y swagger2openapi)
    fi
fi

echo "正在转换为 OpenAPI 3.0 格式..."
if ! "${s2o[@]}" -o "$JSON_FILE" -p "$JSON_FILE"; then
    echo "错误: 转换为 OpenAPI 3.0 失败，产物仍是 Swagger 2.0，fix.py 的处理将不生效"
    exit 1
fi
if ! grep -q '"openapi"[[:space:]]*:' "$JSON_FILE"; then
    echo "错误: 转换后未检测到 openapi 字段，请检查 swagger2openapi 的输出"
    exit 1
fi
echo "已转换为 OpenAPI 3.0 格式：$JSON_FILE"

# 使用 Python 脚本补中文标签、剔除易变字段与 WebSocket 路径，并派生 YAML
python_script="$SCRIPT_DIR/fix.py"
python_cmd=""
if [ -f "$python_script" ]; then
    # 优先使用 Windows 原生 Python（避免 Git Bash 中误用 WSL 的 python3）
    for candidate in python python3; do
        if command -v "$candidate" &> /dev/null; then
            # 验证该 Python 能否访问项目文件
            candidate_path="$(command -v "$candidate")"
            case "$candidate_path" in
                /usr/bin/*|/bin/*) continue ;;  # 跳过 WSL/Linux 系统 Python
            esac
            python_cmd="$candidate"
            break
        fi
    done
    # 如果没找到 Windows 原生 Python，回退到任意可用的 python3
    if [ -z "$python_cmd" ] && command -v python3 &> /dev/null; then
        python_cmd="python3"
    fi
    if [ -z "$python_cmd" ] && command -v python &> /dev/null; then
        python_cmd="python"
    fi
fi

if [ -z "$python_cmd" ] || [ ! -f "$python_script" ]; then
    echo "错误: 未找到可用的 Python，无法补中文标签并派生 YAML 产物"
    echo "请安装 Python 与 PyYAML 后重试: $python_script $JSON_FILE $YAML_FILE"
    exit 1
fi

echo "正在处理产物（中文分组、剔除易变字段与 WebSocket 路径、派生 YAML）... (使用 $python_cmd)"
if ! "$python_cmd" "$python_script" "$JSON_FILE" "$YAML_FILE"; then
    echo "错误: fix.py 执行失败"
    exit 1
fi

# 校验两份产物都是 OpenAPI 3
if ! grep -q '"openapi"[[:space:]]*:' "$JSON_FILE"; then
    echo "错误: $JSON_FILE 不是 OpenAPI 3 格式"
    exit 1
fi
if ! grep -q '^openapi:' "$YAML_FILE"; then
    echo "错误: $YAML_FILE 不是 OpenAPI 3 格式"
    exit 1
fi

echo ""
echo "Swagger文档生成完成！"
echo "JSON文档位置：$JSON_FILE"
echo "YAML文档位置：$YAML_FILE"

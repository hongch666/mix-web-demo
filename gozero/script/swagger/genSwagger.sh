#!/bin/bash
# 生成Swagger文档的脚本 - 使用goctl工具从.api文件生成
#
# goctl 的输出文件名取自 --api 的文件名（main.api -> main.json / main.yaml），
# 因此这里在生成后统一改名为 openapi.json / openapi.yaml

# 脚本目录、GoZero 目录、文档目录
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
# 使用goctl从.api文件生成swagger JSON
goctl api swagger --api main.api --dir "$DOCS_DIR"

# 使用goctl生成swagger YAML
goctl api swagger --api main.api --dir "$DOCS_DIR" --yaml

# goctl 固定输出 main.json / main.yaml，这里按本仓库约定改名
if [ -f "$DOCS_DIR/main.json" ]; then
    mv -f "$DOCS_DIR/main.json" "$JSON_FILE"
fi
if [ -f "$DOCS_DIR/main.yaml" ]; then
    mv -f "$DOCS_DIR/main.yaml" "$YAML_FILE"
fi

# 检查是否成功生成
if [ -f "$JSON_FILE" ] && [ -f "$YAML_FILE" ]; then
    echo "Swagger文档生成完成！"
    echo "JSON文档位置：$JSON_FILE"
    echo "YAML文档位置：$YAML_FILE"

    # 转换为 OpenAPI 3.0 JSON 格式，直接覆盖 openapi.json
    # fix.py 的长连接处理与 servers 清理都按 OpenAPI 3 结构编写，因此这一步是必需的，不再可选
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
        echo "错误: 转换为 OpenAPI 3.0 失败，产物仍是 Swagger 2.0，fix.py 的长连接与 servers 处理将不生效"
        exit 1
    fi
    if grep -q '"openapi"[[:space:]]*:' "$JSON_FILE"; then
        echo "已更新为 OpenAPI 3.0 格式：$JSON_FILE"
    else
        echo "警告: 转换后未检测到 openapi 字段，请检查 swagger2openapi 的输出"
    fi

    # 使用Python脚本为swagger添加中文标签和版本信息，并修复 schemes
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
    if [ -n "$python_cmd" ] && [ -f "$python_script" ]; then
        echo "正在添加中文分组、版本信息和修复 schemes... (使用 $python_cmd)"
        $python_cmd "$python_script" "$JSON_FILE" "$YAML_FILE" || {
            echo "警告: fix.py 执行失败，Swagger 文档已生成但未添加中文标签，请手动运行修复脚本"
        }
    else
        echo "提示: 未找到可用的 Python，跳过中文标签添加"
        echo "如需添加中文标签，请安装 Python 后运行: python3 $python_script $JSON_FILE $YAML_FILE"
    fi
else
    echo "Swagger文档生成失败"
    exit 1
fi

#!/bin/bash
# 生成Swagger文档的脚本 - 使用goctl工具从.api文件生成

# 进入脚本所在目录并记录绝对路径
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

# 进入项目根目录
cd "../.." || exit 1

echo "正在验证goctl工具..."
if ! command -v goctl &> /dev/null
then
    echo "错误: goctl未安装"
    echo "请先安装goctl: go install github.com/zeromicro/go-zero/tools/goctl@latest"
    exit 1
fi

# 创建输出目录
mkdir -p app/docs

# 进入api目录
cd api || exit 1

echo "正在生成Swagger文档..."
# 使用goctl从.api文件生成swagger JSON
goctl api swagger --api main.api --dir ../app/docs

# 使用goctl生成swagger YAML
goctl api swagger --api main.api --dir ../app/docs --yaml

# 检查是否成功生成
if [ -f "../app/docs/main.json" ] && [ -f "../app/docs/main.yaml" ]; then
    echo "Swagger文档生成完成！"
    echo "JSON文档位置：./app/docs/main.json"
    echo "YAML文档位置：./app/docs/main.yaml"

    # 转换为 OpenAPI 3.0 JSON 格式，直接覆盖 main.json
    if command -v swagger2openapi &> /dev/null; then
        echo "正在转换为 OpenAPI 3.0 格式..."
        swagger2openapi -o "../app/docs/main.json" -p "../app/docs/main.json"
        if [ -f "../app/docs/main.json" ]; then
            echo "已更新为 OpenAPI 3.0 格式：./app/docs/main.json"
        fi
    else
        echo "提示: 如需转换为 OpenAPI 3.0 格式，请先安装 swagger2openapi"
        echo "运行: npm install -g swagger2openapi"
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
        $python_cmd "$python_script" "../app/docs/main.json" "../app/docs/main.yaml" || {
            echo "警告: fix.py 执行失败，Swagger 文档已生成但未添加中文标签，请手动运行修复脚本"
        }
    else
        echo "提示: 未找到可用的 Python，跳过中文标签添加"
        echo "如需添加中文标签，请安装 Python 后运行: python3 $python_script app/docs/main.json app/docs/main.yaml"
    fi
else
    echo "Swagger文档生成失败"
    exit 1
fi

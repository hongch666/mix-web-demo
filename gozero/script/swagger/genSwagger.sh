#!/bin/bash
# 生成Swagger文档的脚本 - 使用goctl工具从.api文件生成

# 进入脚本所在目录
cd "$(dirname "$0")" || exit 1

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
    
    # 使用Python脚本为swagger添加中文标签和版本信息
    python_script="$(dirname "$0")/fix.py"
    if [ -f "$python_script" ] && command -v python3 &> /dev/null; then
        echo "正在添加中文分组和版本信息..."
        python3 "$python_script" "../app/docs/main.json" "../app/docs/main.yaml"
    fi
    
    # 清理api目录下可能残留的文件
    rm -f main.json main.yaml
    
    echo ""
    echo "可选: 转换为OpenAPI3格式"
    echo "运行: npm install -g swagger2openapi && swagger2openapi -o ../app/docs/main-openapi3.yaml -p ../app/docs/main.json"
else
    echo "Swagger文档生成失败"
    exit 1
fi

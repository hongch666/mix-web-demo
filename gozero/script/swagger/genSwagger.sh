#!/bin/bash
# 生成Swagger文档的脚本

# 检查swag是否安装
if ! command -v swag &> /dev/null
then
    echo "swag未安装，正在安装..."
    go install github.com/swaggo/swag/cmd/swag@latest
fi

# 进入app目录
cd "$(dirname "$0")/../../app"

echo "正在生成Swagger文档..."
# 使用 -g 参数指定包含swagger注释的文件
swag init -g internal/handler/routes.go

echo "Swagger文档生成完成！"
echo "文档位置：./docs/"

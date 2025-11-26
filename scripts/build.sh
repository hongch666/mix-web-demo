#!/bin/bash

# 获取脚本所在目录的父目录（项目根目录）
WORKDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$WORKDIR"

echo "================================"
echo "Starting build process..."
echo "================================"

# 清理dist目录
if [ -d "dist" ]; then
    rm -rf dist
    echo "Cleaned dist directory"
fi

# 创建dist目录
mkdir -p dist

# ==================== Spring ====================
echo ""
echo "================================"
echo "Building Spring service..."
echo "================================"
cd "$WORKDIR/spring"
mvn clean install -q
if [ $? -eq 0 ]; then
    echo "✓ Spring built successfully"
    mkdir -p "$WORKDIR/dist/spring"
    cp -r src target pom.xml mvnw mvnw.cmd "$WORKDIR/dist/spring/"
else
    echo "✗ Spring build failed"
    exit 1
fi

# ==================== Gateway ====================
echo ""
echo "================================"
echo "Building Gateway..."
echo "================================"
cd "$WORKDIR/gateway"
mvn clean install -q
if [ $? -eq 0 ]; then
    echo "✓ Gateway built successfully"
    mkdir -p "$WORKDIR/dist/gateway"
    cp -r src target pom.xml mvnw mvnw.cmd "$WORKDIR/dist/gateway/"
else
    echo "✗ Gateway build failed"
    exit 1
fi

# ==================== Gin ====================
echo ""
echo "================================"
echo "Building Gin service..."
echo "================================"
cd "$WORKDIR/gin"
go build -o gozero_service . 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✓ Gin built successfully"
    mkdir -p "$WORKDIR/dist/gin"
    cp -r . "$WORKDIR/dist/gin/" --exclude=dist --exclude=.git --exclude=vendor 2>/dev/null
else
    echo "✗ Gin build failed"
    exit 1
fi

# ==================== NestJS ====================
echo ""
echo "================================"
echo "Building NestJS service..."
echo "================================"
cd "$WORKDIR/nestjs"
npm run build >/dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✓ NestJS built successfully"
    mkdir -p "$WORKDIR/dist/nestjs"
    cp -r dist node_modules package.json "$WORKDIR/dist/nestjs/"
else
    echo "✗ NestJS build failed"
    exit 1
fi

# ==================== FastAPI ====================
echo ""
echo "================================"
echo "Building FastAPI service..."
echo "================================"
cd "$WORKDIR/fastapi"
# FastAPI不需要编译，只需要复制文件
if [ -f "main.py" ]; then
    echo "✓ FastAPI prepared"
    mkdir -p "$WORKDIR/dist/fastapi"
    cp -r . "$WORKDIR/dist/fastapi/" --exclude=.venv --exclude=__pycache__ --exclude=.git 2>/dev/null
else
    echo "✗ FastAPI not found"
    exit 1
fi

# ==================== GoZero ====================
echo ""
echo "================================"
echo "Building GoZero service..."
echo "================================"
cd "$WORKDIR/gozero"
go build -o gozero_service . 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✓ GoZero built successfully"
    mkdir -p "$WORKDIR/dist/gozero"
    cp -r . "$WORKDIR/dist/gozero/" --exclude=dist --exclude=.git --exclude=vendor 2>/dev/null
else
    echo "✗ GoZero build failed"
    exit 1
fi

echo ""
echo "================================"
echo "Build completed successfully!"
echo "================================"
echo ""
echo "Distribution files are in: $WORKDIR/dist/"

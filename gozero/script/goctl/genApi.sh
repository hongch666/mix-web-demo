#!/bin/bash

# script should be execute in current `script` directory.

# Usage: ./genApi.sh [-s]
#   -s : also run swagger generation and convert to OpenAPI3

generate_swagger=false

while [[ $# -gt 0 ]]; do
	case $1 in
		-s)
			generate_swagger=true
			shift
			;;
		*)
			echo "Unknown option: $1"
			exit 1
			;;
	esac
done

# Save the original location
original_location=$(pwd)

# Change to the target directory
cd "$(dirname "$(readlink -f "$0")")/../.." || exit 1

# Setup variables
app_dir="$PWD/app"
main_go_file="$app_dir/main.go"
etc_dir="$app_dir/etc"
backup_dir="$(mktemp -d)"

# Ensure temporary backup directory cleanup
cleanup() {
	rm -rf "$backup_dir"
}
trap cleanup EXIT

# Backup main.go
if [ -f "$main_go_file" ]; then
	cp "$main_go_file" "$backup_dir/main.go"
	echo "Backed up main.go"
fi

# Backup etc directory
if [ -d "$etc_dir" ]; then
	rm -rf "$backup_dir/etc"
	cp -r "$etc_dir" "$backup_dir/etc"
	echo "Backed up etc directory"
fi

cd api || exit 1

# format api files
echo "Formatting API files..."
goctl api format -dir .

# generate go-zero code
echo "Generating go-zero code..."
goctl api go -api main.api -dir ../app --style=goZero

# Remove generated app.go (we use main.go as entry)
if [ -f "$app_dir/app.go" ]; then
	rm "$app_dir/app.go"
	echo "Removed generated app.go"
fi

# 在 routes.go 文件顶部插入 Swagger 注释
routes_file="$app_dir/internal/handler/routes.go"
if [ -f "$routes_file" ]; then
	echo "Adding Swagger documentation to routes.go..."
	
	# 创建临时文件
	temp_routes=$(mktemp)
	
	# 写入 Swagger 注释
	cat > "$temp_routes" << 'EOF'
// @title GoZero部分的Swagger文档
// @description 这是项目的GoZero部分的Swagger文档
// @version 1.0.0
// @host localhost:8082
// @basePath /

EOF
	
	# 追加原有的路由文件内容，同时移除 goctl 生成的两行注释和空行
	tail -n +4 "$routes_file" >> "$temp_routes"
	
	# 替换原文件
	mv "$temp_routes" "$routes_file"
	echo "Swagger documentation added to routes.go"
fi

# Restore main.go
if [ -f "$backup_dir/main.go" ]; then
	cp "$backup_dir/main.go" "$main_go_file"
	echo "Restored main.go"
fi

# Restore etc directory
if [ -d "$backup_dir/etc" ]; then
	rm -rf "$etc_dir"
	cp -r "$backup_dir/etc" "$etc_dir"
	echo "Restored etc directory"
fi

# generate swagger and convert to openapi3 only when -s is provided
if [ "$generate_swagger" = true ]; then
	echo "Generating Swagger documentation..."
	goctl api swagger --api main.api --dir .

	echo "Converting Swagger to OpenAPI3..."
	npx swagger2openapi -o main.yaml -p main.json
else
	echo "Skipping swagger and openapi conversion (pass -s to execute)."
fi

# Restore original location
cd "$original_location" || exit 1

echo "Done!"

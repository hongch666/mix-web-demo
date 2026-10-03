#!/bin/bash

# script should be execute in current `script` directory.

# Usage: ./genApi.sh [-s] [--template <path>]
#   -s : also run swagger generation and convert to OpenAPI3
#   --template <path> : goctl template home, defaults to gozero/template

generate_swagger=false
template_home=""

while [[ $# -gt 0 ]]; do
	case $1 in
		-s)
			generate_swagger=true
			shift
			;;
		--template)
			template_home="$2"
			shift 2
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
gozero_root="$PWD"
repo_root="$(cd "$gozero_root/.." && pwd)"
app_dir="$gozero_root/app"
main_go_file="$app_dir/main.go"
etc_dir="$app_dir/etc"
backup_dir="$(mktemp -d)"
if [ -z "$template_home" ]; then
	template_home="$PWD/template"
fi
template_home="$(cd "$template_home" && pwd)"

# Ensure temporary backup directory cleanup
cleanup() {
	rm -rf "$backup_dir"
}
trap cleanup EXIT

# ==================== 清理 goctl 生成的小写中间件骨架 ====================
# goctl 会把 .api 里声明的 XxxMiddleware 统一转成小写开头的文件名（如 userContextMiddleware 变成
# usercontextMiddleware.go），与仓库手写的 camelCase 文件重名，导致中间件构造函数重复声明、编译失败。
# 这里只删除同时满足三个条件的文件，三个条件缺一不可，避免误删真实实现：
#   1. 位于 app/internal/middleware 目录下
#   2. 同目录存在忽略大小写后同名的另一个文件
#   3. 文件内容含 goctl 空骨架的占位注释，说明它确实是 goctl 生成的而非手写的
# 大小写转换全部用 shell 内建展开，不依赖 basename、tr 等外部命令
remove_lowercase_middleware_skeletons() {
	local middleware_dir="$app_dir/internal/middleware"
	[ -d "$middleware_dir" ] || return 0

	local file sibling base lower sibling_base sibling_lower kept
	for file in "$middleware_dir"/*.go; do
		[ -e "$file" ] || continue
		grep -q "TODO generate middleware implement function" "$file" || continue

		base="${file##*/}"
		lower="${base,,}"
		kept=""
		for sibling in "$middleware_dir"/*.go; do
			[ -e "$sibling" ] || continue
			[ "$sibling" = "$file" ] && continue
			sibling_base="${sibling##*/}"
			[ "$sibling_base" = "$base" ] && continue
			sibling_lower="${sibling_base,,}"
			if [ "$sibling_lower" = "$lower" ]; then
				kept="$sibling_base"
				break
			fi
		done

		if [ -n "$kept" ]; then
			rm -f "$file"
			echo "Removed goctl middleware skeleton: $base (kept $kept)"
		fi
	done
}

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
goctl api go -api main.api -dir ../app --style=goZero --home "$template_home"

# Remove or promote generated app.go (we use main.go as entry)
if [ -f "$app_dir/app.go" ]; then
	if [ -f "$backup_dir/main.go" ]; then
		rm "$app_dir/app.go"
		echo "Removed generated app.go"
	else
		mv "$app_dir/app.go" "$main_go_file"
		echo "Moved generated app.go to main.go"
	fi
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

# Remove the lowercase middleware skeletons goctl generated for camelCase implementations
remove_lowercase_middleware_skeletons

# Format generated code so routes.go, types.go and new handlers keep the project format
format_script="$repo_root/scripts/format.sh"
if [ -f "$format_script" ]; then
	echo "Formatting generated code..."
	if ! bash "$format_script" gozero; then
		echo "Formatting failed, please run ./mix format gozero manually" >&2
		exit 1
	fi
else
	echo "scripts/format.sh not found, skip formatting, please run ./mix format gozero manually" >&2
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

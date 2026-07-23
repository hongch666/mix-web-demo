#!/bin/bash

execute=false
srcDir="gozero/script/sql"
outDir="./gozero/app/model"
pattern="*.sql"
template_home=""

while [[ $# -gt 0 ]]; do
	case $1 in
		-s) execute=true; shift ;;
		-srcDir) srcDir="$2"; shift 2 ;;
		-outDir) outDir="$2"; shift 2 ;;
		-pattern) pattern="$2"; shift 2 ;;
		--template) template_home="$2"; shift 2 ;;
		*) echo "Unknown option: $1"; exit 1 ;;
	esac
done

lower_camel() {
	local upper
	upper="$(awk -F'_' '{ for (i = 1; i <= NF; i++) printf "%s%s", toupper(substr($i, 1, 1)), substr($i, 2) }' <<<"$1")"
	printf "%s%s" "$(tr '[:upper:]' '[:lower:]' <<<"${upper:0:1}")" "${upper:1}"
}

extract_table_name() {
	sed -nE 's/^[[:space:]]*CREATE[[:space:]]+TABLE([[:space:]]+IF[[:space:]]+NOT[[:space:]]+EXISTS)?[[:space:]]+`?([A-Za-z0-9_]+)`?.*/\2/Ip' "$1" | head -n 1
}

script_dir=$(dirname "$(readlink -f "$0")")
repo_root=$(cd "$script_dir/../../.." && pwd)
cd "$repo_root" || exit 1
if [ -z "$template_home" ]; then template_home="$repo_root/gozero/template"; fi
template_home="$(cd "$template_home" && pwd)"

while IFS= read -r -d '' file; do
	table="$(extract_table_name "$file")"
	if [ -n "$table" ]; then target_dir="$outDir/$(lower_camel "$table")"; else target_dir="$outDir"; fi
	args=("model" "mysql" "ddl" "--style" "goZero" "--home" "$template_home" "--src" "$file" "--dir" "$target_dir")
	if [ "$execute" = true ]; then goctl "${args[@]}"; else echo "Dry-run (pass -s to execute): goctl ${args[*]}"; fi
done < <(find "$srcDir" -maxdepth 1 -name "$pattern" -type f -print0)

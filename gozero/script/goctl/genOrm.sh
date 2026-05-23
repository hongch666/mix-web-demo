#!/bin/bash

# script should be execute in current `script` directory.

# Usage: ./genOrm.sh [-s] [--gorm] [-srcDir <path>] [-outDir <path>] [-pattern <glob>] [--template <path>]
#   -s : actually execute the generated goctl commands; otherwise the script runs in dry-run mode and prints commands.
#   --gorm : generate the project GormCrud custom model shell for new model files.
#   --template <path> : goctl template home, defaults to gozero/template

execute=false
generate_gorm=false
srcDir="gozero/script/sql"
outDir="./gozero/app/model"
pattern="*.sql"
template_home=""

while [[ $# -gt 0 ]]; do
	case $1 in
		-s)
			execute=true
			shift
			;;
		--gorm)
			generate_gorm=true
			shift
			;;
		-srcDir)
			srcDir="$2"
			shift 2
			;;
		-outDir)
			outDir="$2"
			shift 2
			;;
		-pattern)
			pattern="$2"
			shift 2
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

upper_camel() {
	local value="$1"
	awk -F'_' '{
		for (i = 1; i <= NF; i++) {
			printf "%s%s", toupper(substr($i, 1, 1)), substr($i, 2)
		}
	}' <<<"$value"
}

lower_camel() {
	local upper
	upper="$(upper_camel "$1")"
	printf "%s%s" "$(tr '[:upper:]' '[:lower:]' <<<"${upper:0:1}")" "${upper:1}"
}

extract_table_name() {
	sed -nE 's/^[[:space:]]*CREATE[[:space:]]+TABLE([[:space:]]+IF[[:space:]]+NOT[[:space:]]+EXISTS)?[[:space:]]+`?([A-Za-z0-9_]+)`?.*/\2/Ip' "$1" | head -n 1
}

extract_id_type() {
	sed -nE 's/^[[:space:]]*`?id`?[[:space:]]+([^[:space:],]+).*/\1/Ip' "$1" | head -n 1 |
		awk '{ v=tolower($0); if (v ~ /unsigned/) print "uint64"; else print "int64" }'
}

write_gorm_model() {
	local sql_file="$1"
	local table object lower id_type model_dir model_file
	table="$(extract_table_name "$sql_file")"
	if [ -z "$table" ]; then
		echo "Skip Gorm model: cannot parse table name from $sql_file"
		return 0
	fi
	object="$(upper_camel "$table")"
	lower="$(lower_camel "$table")"
	id_type="$(extract_id_type "$sql_file")"
	if [ -z "$id_type" ]; then
		id_type="int64"
	fi
	model_dir="$outDir/$lower"
	model_file="$model_dir/${lower}Model.go"

	if [ -f "$model_file" ] && ! grep -q "default${object}Model: new${object}Model" "$model_file"; then
		echo "Skip Gorm model: $model_file already exists"
		return 0
	fi
	if [ "$execute" != true ]; then
		echo "Dry-run (pass -s to execute): generate Gorm model shell $model_file"
		return 0
	fi

	mkdir -p "$model_dir"
	cat >"$model_file" <<EOF
package $lower

import (
	"context"

	"app/model"

	"gorm.io/gorm"
)

var _ ${object}Model = (*custom${object}Model)(nil)

type (
	${object}Model interface {
		Insert(ctx context.Context, data *${object}) error
		FindOne(ctx context.Context, id ${id_type}) (*${object}, error)
		Update(ctx context.Context, data *${object}) error
		Delete(ctx context.Context, id ${id_type}) error
	}

	custom${object}Model struct {
		crud *model.GormCrud[${object}]
	}
)

// New${object}Model returns a model for the database table.
func New${object}Model(db *gorm.DB) ${object}Model {
	return &custom${object}Model{
		crud: model.NewGormCrud[${object}](db, "$table"),
	}
}

func (m *custom${object}Model) Insert(ctx context.Context, data *${object}) error {
	return m.crud.Insert(ctx, data)
}

func (m *custom${object}Model) FindOne(ctx context.Context, id ${id_type}) (*${object}, error) {
	return m.crud.FindOne(ctx, id)
}

func (m *custom${object}Model) Update(ctx context.Context, data *${object}) error {
	return m.crud.Update(ctx, data.Id, data)
}

func (m *custom${object}Model) Delete(ctx context.Context, id ${id_type}) error {
	return m.crud.Delete(ctx, id)
}
EOF
	gofmt -w "$model_file"
	echo "Generated Gorm model shell: $model_file"
}

# Save the original location
original_location=$(pwd)

# Change to the repository root (three levels up from genOrm.sh)
script_dir=$(dirname "$(readlink -f "$0")")
repo_root=$(cd "$script_dir/../../.." && pwd)
cd "$repo_root" || exit 1
if [ -z "$template_home" ]; then
	template_home="$repo_root/gozero/template"
fi
template_home="$(cd "$template_home" && pwd)"

# Resolve full source path
if [ ! -d "$srcDir" ]; then
	echo "Source directory '$srcDir' not found. Aborting."
	echo "Current working directory: $(pwd)"
	echo "Expected path: $srcDir"
	cd "$original_location" || exit 1
	exit 1
fi

# Collect matching SQL files
files=()
while IFS= read -r -d '' file; do
	files+=("$file")
done < <(find "$srcDir" -maxdepth 1 -name "$pattern" -type f -print0)

if [ ${#files[@]} -eq 0 ]; then
	echo "No files matching '$pattern' found in '$srcDir'. Nothing to do."
	cd "$original_location" || exit 1
	exit 0
fi

echo "Found ${#files[@]} files in $srcDir matching pattern '$pattern'."

for f in "${files[@]}"; do
	table="$(extract_table_name "$f")"
	if [ -n "$table" ]; then
		target_dir="$outDir/$(lower_camel "$table")"
	else
		target_dir="$outDir"
	fi
	exe="goctl"
	args=("model" "mysql" "ddl" "--style" "goZero" "--home" "$template_home" "--src" "$f" "--dir" "$target_dir")
	cmdLine="$exe ${args[*]}"

	if [ "$execute" = true ]; then
		echo "Executing: $cmdLine"
		$exe "${args[@]}"
		if [ $? -ne 0 ]; then
			echo "Command failed for file: $f (exit code $?)"
		fi
	else
		echo "Dry-run (pass -s to execute): $cmdLine"
	fi

	if [ "$generate_gorm" = true ]; then
		write_gorm_model "$f"
	fi
done

# Restore original location
cd "$original_location" || exit 1

echo "Done!"

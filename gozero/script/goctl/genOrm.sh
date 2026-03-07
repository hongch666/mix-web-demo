#!/bin/bash

# script should be execute in current `script` directory.

# Usage: ./genOrm.sh [-s] [-srcDir <path>] [-outDir <path>] [-pattern <glob>]
#   -s : actually execute the generated goctl commands; otherwise the script runs in dry-run mode and prints commands.

execute=false
srcDir="gozero/script/sql"
outDir="./gozero/app/model"
pattern="*.sql"

while [[ $# -gt 0 ]]; do
	case $1 in
		-s)
			execute=true
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
		*)
			echo "Unknown option: $1"
			exit 1
			;;
	esac
done

# Save the original location
original_location=$(pwd)

# Change to the repository root (three levels up from genOrm.sh)
script_dir=$(dirname "$(readlink -f "$0")")
repo_root=$(cd "$script_dir/../../.." && pwd)
cd "$repo_root" || exit 1

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
	exe="goctl"
	args=("model" "mysql" "ddl" "--style" "goZero" "--src" "$f" "--dir" "$outDir")
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
done

# Restore original location
cd "$original_location" || exit 1

echo "Done!"

# script should be execute in current `script` directory.

# Usage: ./genApi.ps1 [-s] [-template <path>]
#   -s : also run swagger generation and convert to OpenAPI3

param(
	[switch]$s,
	[string]$template = ""
)

# Save the original location
$originalLocation = Get-Location

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$gozeroRoot = Resolve-Path (Join-Path $scriptDir "../..")
if ([string]::IsNullOrWhiteSpace($template)) {
	$template = Join-Path $gozeroRoot "template"
}
$templateHome = (Resolve-Path $template).Path

# Change to the target directory
Set-Location -Path (Join-Path $gozeroRoot "api")

# format api files
goctl api format -dir .

# Backup important files before generation
$appDir = Resolve-Path "../app"
$mainGoFile = Join-Path $appDir "main.go"
$etcDir = Join-Path $appDir "etc"
$backupDir = Join-Path $env:TEMP ("goctl-api-backup-" + [Guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $backupDir | Out-Null

# Backup main.go
if (Test-Path $mainGoFile) {
	Copy-Item $mainGoFile (Join-Path $backupDir "main.go") -Force | Out-Null
	Write-Host "Backed up main.go"
}

# Backup etc directory
if (Test-Path $etcDir) {
	$etcBackup = Join-Path $backupDir "etc"
	if (Test-Path $etcBackup) {
		Remove-Item $etcBackup -Recurse -Force | Out-Null
	}
	Copy-Item $etcDir $etcBackup -Recurse -Force | Out-Null
	Write-Host "Backed up etc directory"
}

# generate go-zero code
goctl api go -api main.api -dir ../app --style=goZero --home $templateHome

# Remove or promote generated app.go (we use main.go as entry)
$appGoFile = Join-Path $appDir "app.go"
if (Test-Path $appGoFile) {
	if (Test-Path (Join-Path $backupDir "main.go")) {
		Remove-Item $appGoFile -Force | Out-Null
		Write-Host "Removed generated app.go"
	} else {
		Move-Item $appGoFile $mainGoFile -Force | Out-Null
		Write-Host "Moved generated app.go to main.go"
	}
}

# Restore main.go and etc directory
if (Test-Path (Join-Path $backupDir "main.go")) {
	Copy-Item (Join-Path $backupDir "main.go") $mainGoFile -Force | Out-Null
	Write-Host "Restored main.go"
}

if (Test-Path (Join-Path $backupDir "etc")) {
	if (Test-Path $etcDir) {
		Remove-Item $etcDir -Recurse -Force | Out-Null
	}
	Copy-Item (Join-Path $backupDir "etc") $etcDir -Recurse -Force | Out-Null
	Write-Host "Restored etc directory"
}

# ==================== 清理 goctl 生成的小写中间件骨架 ====================
# goctl 会把 .api 里声明的 XxxMiddleware 统一转成小写开头的文件名（如 userContextMiddleware 变成
# usercontextMiddleware.go），与仓库手写的 camelCase 文件重名，导致中间件构造函数重复声明、编译失败。
# 判定条件与 genApi.sh 一致，三个条件缺一不可，避免误删真实实现：
#   1. 位于 app/internal/middleware 目录下
#   2. 同目录存在忽略大小写后同名的另一个文件
#   3. 文件内容含 goctl 空骨架的占位注释，说明它确实是 goctl 生成的而非手写的
function Remove-LowercaseMiddlewareSkeleton {
	param([string]$MiddlewareDir)

	if (-not (Test-Path $MiddlewareDir)) { return }

	$files = @(Get-ChildItem -Path $MiddlewareDir -Filter *.go -File)
	foreach ($file in $files) {
		$content = Get-Content -Path $file.FullName -Raw
		if ($content -notmatch "TODO generate middleware implement function") { continue }

		$lower = $file.Name.ToLowerInvariant()
		$kept = $files | Where-Object {
			$_.FullName -ne $file.FullName -and
			$_.Name -ne $file.Name -and
			$_.Name.ToLowerInvariant() -eq $lower
		} | Select-Object -First 1

		if ($null -ne $kept) {
			Remove-Item -Path $file.FullName -Force
			Write-Host ("Removed goctl middleware skeleton: " + $file.Name + " (kept " + $kept.Name + ")")
		}
	}
}

# Remove the lowercase middleware skeletons goctl generated for camelCase implementations
Remove-LowercaseMiddlewareSkeleton -MiddlewareDir (Join-Path $appDir "internal\middleware")

# Format generated code so routes.go, types.go and new handlers keep the project format
# scripts/format.sh 是 bash 脚本，Windows 下直接调用同一个底层工具 golangci-lint fmt
if (Get-Command golangci-lint -ErrorAction SilentlyContinue) {
	Write-Host "Formatting generated code..."
	Push-Location (Join-Path $gozeroRoot "app")
	golangci-lint fmt
	$formatExitCode = $LASTEXITCODE
	Pop-Location
	if ($formatExitCode -ne 0) {
		Write-Host "Formatting failed, please run ./mix format gozero manually"
		exit 1
	}
} else {
	Write-Host "golangci-lint not found, skip formatting, please run ./mix format gozero manually"
}

# Remove temporary backup directory
if (Test-Path $backupDir) {
	Remove-Item $backupDir -Recurse -Force | Out-Null
}

# generate swagger and convert to openapi3 only when -s is provided
if ($s) {
	# generate swagger
	goctl api swagger --api main.api --dir .

	# swagger to openapi3
	npx swagger2openapi -o main.yaml -p main.json
} else {
	Write-Host "Skipping swagger and openapi conversion (pass -s to execute)."
}

# Restore original location (optional but good practice)
Set-Location -Path $originalLocation

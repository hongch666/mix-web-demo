param(
	[switch]$s,
	[string]$srcDir = "gozero/script/sql",
	[string]$outDir = "./gozero/app/model",
	[string]$pattern = "*.sql",
	[string]$template = ""
)

function Convert-ToLowerCamel([string]$value) {
	$upper = (($value -split "_") | ForEach-Object { $_.Substring(0, 1).ToUpper() + $_.Substring(1) }) -join ""
	return $upper.Substring(0, 1).ToLower() + $upper.Substring(1)
}

function Get-TableName([string]$file) {
	foreach ($line in Get-Content -LiteralPath $file) {
		if ($line -match '^\s*CREATE\s+TABLE(\s+IF\s+NOT\s+EXISTS)?\s+`?([A-Za-z0-9_]+)`?') { return $Matches[2] }
	}
	return ""
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Resolve-Path (Join-Path $scriptDir "../../..")
Set-Location -Path $repoRoot
if ([string]::IsNullOrWhiteSpace($template)) { $template = Join-Path $repoRoot "gozero/template" }
$templateHome = (Resolve-Path $template).Path

foreach ($file in Get-ChildItem -Path $srcDir -Filter $pattern -File) {
	$table = Get-TableName $file.FullName
	$targetDir = if ([string]::IsNullOrWhiteSpace($table)) { $outDir } else { Join-Path $outDir (Convert-ToLowerCamel $table) }
	$args = @("model", "mysql", "ddl", "--style", "goZero", "--home", $templateHome, "--src", $file.FullName, "--dir", $targetDir)
	if ($s) { & goctl @args } else { Write-Host "Dry-run (pass -s to execute): goctl $($args -join ' ')" }
}

# 实际执行生成后才格式化，dry-run 模式下没有文件变更无需格式化
# scripts/format.sh 是 bash 脚本，Windows 下直接调用同一个底层工具 golangci-lint fmt
if ($s) {
	if (Get-Command golangci-lint -ErrorAction SilentlyContinue) {
		Write-Host "Formatting generated code..."
		Push-Location (Join-Path $repoRoot "gozero/app")
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
}

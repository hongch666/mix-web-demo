# script should be execute in current `script` directory.

# Usage: ./genOrm.ps1 [-s] [-gorm] [-srcDir <path>] [-outDir <path>] [-pattern <glob>] [-template <path>]
#   -s : actually execute the generated goctl commands; otherwise the script runs in dry-run mode and prints commands.

param(
	[switch]$s,
	[switch]$gorm,
	[string]$srcDir = "gozero/script/sql",
	[string]$outDir = "./gozero/app/model",
	[string]$pattern = "*.sql",
	[string]$template = ""
)

function Convert-ToUpperCamel([string]$value) {
	return (($value -split "_") | ForEach-Object {
		if ($_.Length -eq 0) { "" } else { $_.Substring(0,1).ToUpper() + $_.Substring(1) }
	}) -join ""
}

function Convert-ToLowerCamel([string]$value) {
	$upper = Convert-ToUpperCamel $value
	if ($upper.Length -eq 0) { return "" }
	return $upper.Substring(0,1).ToLower() + $upper.Substring(1)
}

function Get-TableName([string]$file) {
	$content = Get-Content -LiteralPath $file
	foreach ($line in $content) {
		if ($line -match '^\s*CREATE\s+TABLE(\s+IF\s+NOT\s+EXISTS)?\s+`?([A-Za-z0-9_]+)`?') {
			return $Matches[2]
		}
	}
	return ""
}

function Get-IdType([string]$file) {
	$content = Get-Content -LiteralPath $file
	foreach ($line in $content) {
		if ($line -match '^\s*`?id`?\s+([^,\s]+)') {
			if ($line.ToLower().Contains("unsigned")) { return "uint64" }
			return "int64"
		}
	}
	return "int64"
}

function Write-GormModel([string]$sqlFile) {
	$table = Get-TableName $sqlFile
	if ([string]::IsNullOrWhiteSpace($table)) {
		Write-Host "Skip Gorm model: cannot parse table name from $sqlFile" -ForegroundColor Yellow
		return
	}
	$object = Convert-ToUpperCamel $table
	$lower = Convert-ToLowerCamel $table
	$idType = Get-IdType $sqlFile
	$modelDir = Join-Path $outDir $lower
	$modelFile = Join-Path $modelDir "$($lower)Model.go"

	if ((Test-Path $modelFile) -and -not ((Get-Content -LiteralPath $modelFile -Raw) -match "default${object}Model: new${object}Model")) {
		Write-Host "Skip Gorm model: $modelFile already exists"
		return
	}
	if (-not $s) {
		Write-Host "Dry-run (pass -s to execute): generate Gorm model shell $modelFile"
		return
	}

	New-Item -ItemType Directory -Path $modelDir -Force | Out-Null
	@"
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
		FindOne(ctx context.Context, id ${idType}) (*${object}, error)
		Update(ctx context.Context, data *${object}) error
		Delete(ctx context.Context, id ${idType}) error
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

func (m *custom${object}Model) FindOne(ctx context.Context, id ${idType}) (*${object}, error) {
	return m.crud.FindOne(ctx, id)
}

func (m *custom${object}Model) Update(ctx context.Context, data *${object}) error {
	return m.crud.Update(ctx, data.Id, data)
}

func (m *custom${object}Model) Delete(ctx context.Context, id ${idType}) error {
	return m.crud.Delete(ctx, id)
}
"@ | Set-Content -Path $modelFile -Encoding utf8
	gofmt -w $modelFile
	Write-Host "Generated Gorm model shell: $modelFile" -ForegroundColor Green
}

# Save the original location
$originalLocation = Get-Location

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Resolve-Path (Join-Path $scriptDir "../../..")

# Change to the repository root
Set-Location -Path $repoRoot
if ([string]::IsNullOrWhiteSpace($template)) {
	$template = Join-Path $repoRoot "gozero/template/goctl"
}
$templateHome = (Resolve-Path $template).Path

# Resolve full source path
$fullSrc = Resolve-Path -LiteralPath $srcDir -ErrorAction SilentlyContinue
if (-not $fullSrc) {
	Write-Host "Source directory '$srcDir' not found. Aborting." -ForegroundColor Red
	Set-Location -Path $originalLocation
	exit 1
}

# Collect matching SQL files
$files = Get-ChildItem -Path $fullSrc -Filter $pattern -File -ErrorAction SilentlyContinue
if (-not $files -or $files.Count -eq 0) {
	Write-Host "No files matching '$pattern' found in '$fullSrc'. Nothing to do." -ForegroundColor Yellow
	Set-Location -Path $originalLocation
	exit 0
}

Write-Host "Found $($files.Count) files in $fullSrc matching pattern '$pattern'." -ForegroundColor Cyan

foreach ($f in $files) {
	$table = Get-TableName $f.FullName
	if ([string]::IsNullOrWhiteSpace($table)) {
		$targetDir = $outDir
	} else {
		$targetDir = Join-Path $outDir (Convert-ToLowerCamel $table)
	}
	$exe = "goctl"
	$args = @("model","mysql","ddl","--style","goZero","--home",$templateHome,"--src",$f.FullName,"--dir",$targetDir)
	$cmdLine = "$exe $($args -join ' ')"

	if ($s) {
		Write-Host "Executing: $cmdLine" -ForegroundColor Green
		& $exe @args
		if ($LASTEXITCODE -ne 0) {
			Write-Host "Command failed for file: $($f.FullName) (exit code $LASTEXITCODE)" -ForegroundColor Red
			# continue to next file rather than aborting everything
		}
	} else {
		Write-Host "Dry-run (pass -s to execute): $cmdLine"
	}

	if ($gorm) {
		Write-GormModel $f.FullName
	}
}

# Restore original location (optional but good practice)
Set-Location -Path $originalLocation

# script should be execute in current `script` directory.

# Usage: ./genApi.ps1 [-s]
#   -s : also run swagger generation and convert to OpenAPI3

param(
	[switch]$s
)

# Save the original location
$originalLocation = Get-Location

# Change to the target directory
Set-Location -Path (Resolve-Path "../../api")

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
goctl api go -api main.api -dir ../app --style=goZero

# Remove generated app.go (we use main.go as entry)
$appGoFile = Join-Path $appDir "app.go"
if (Test-Path $appGoFile) {
	Remove-Item $appGoFile -Force | Out-Null
	Write-Host "Removed generated app.go"
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

# script should be execute in current `script` directory.

# Usage: ./genOrm.ps1 [-s] [-srcDir <path>] [-outDir <path>] [-pattern <glob>]
#   -s : actually execute the generated goctl commands; otherwise the script runs in dry-run mode and prints commands.

param(
	[switch]$s,
	[string]$srcDir = "gozero/script/sql",
	[string]$outDir = "./gozero/app/model",
	[string]$pattern = "*.sql"
)

# Save the original location
$originalLocation = Get-Location

# Change to the repository root (two levels up)
Set-Location -Path (Resolve-Path "../../")

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
	$exe = "goctl"
	$args = @("model","mysql","ddl","--style","goZero","--src",$f.FullName,"--dir",$outDir)
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
}

# Restore original location (optional but good practice)
Set-Location -Path $originalLocation

# PowerShell 脚本：生成 GoZero 的 Swagger/OpenAPI 文档 - 使用 goctl 从 .api 生成
#
# 流程与 genSwagger.sh 一致：
#   1. goctl 生成 main.json，按仓库约定改名为 openapi.json
#   2. swagger2openapi 转换为 OpenAPI 3.0（必需，未安装则自动安装）
#   3. fix.py 补中文标签、剔除易变字段与 WebSocket 路径，并由处理后的 JSON 派生 openapi.yaml
#
# YAML 不由 goctl 单独生成：那样会停留在 Swagger 2.0，与已是 OpenAPI 3 的 JSON 格式分叉

# 必须用 $PSScriptRoot：$MyInvocation.MyCommand.Path 在被相对路径调用时可能是相对目录，
# 会让产物落到错误位置（曾出现 gozero/api/gozero/app/docs 这种嵌套冗余目录）
$scriptPath = $PSScriptRoot
$projectRoot = (Resolve-Path (Join-Path $scriptPath "..\..")).Path
$apiPath = Join-Path $projectRoot "api"
$appPath = Join-Path $projectRoot "app"
$docsPath = Join-Path $appPath "docs"
$jsonPath = Join-Path $docsPath "openapi.json"
$yamlPath = Join-Path $docsPath "openapi.yaml"

Write-Host "正在验证goctl工具..."
$goctl = Get-Command goctl -ErrorAction SilentlyContinue
if ($null -eq $goctl) {
    Write-Host "错误: goctl未安装"
    Write-Host "请先安装goctl: go install github.com/zeromicro/go-zero/tools/goctl@latest"
    exit 1
}

# 创建输出目录
if (-not (Test-Path $docsPath)) {
    New-Item -ItemType Directory -Path $docsPath | Out-Null
}

Write-Host "切换到API目录..."
Push-Location $apiPath

Write-Host "正在生成Swagger文档..."
goctl api swagger --api main.api --dir $docsPath

# goctl 固定输出 main.json，这里按本仓库约定改名
$generatedJson = Join-Path $docsPath "main.json"
if (Test-Path $generatedJson) {
    Move-Item -Force $generatedJson $jsonPath
}
# 清理历史遗留的 main.yaml，避免与派生产物混淆
Remove-Item -Path (Join-Path $docsPath "main.yaml") -Force -ErrorAction SilentlyContinue

if (-not (Test-Path $jsonPath)) {
    Write-Host "Swagger文档生成失败"
    Pop-Location
    exit 1
}
Write-Host "goctl 生成完成：$jsonPath"

# 转换为 OpenAPI 3.0：未安装时自动安装；装完仍不在 PATH 时退化为 npx 调用
$s2o = Get-Command swagger2openapi -ErrorAction SilentlyContinue
if ($null -eq $s2o) {
    Write-Host "未检测到 swagger2openapi，正在自动安装..."
    if ($null -eq (Get-Command npm -ErrorAction SilentlyContinue)) {
        Write-Host "错误: 自动安装需要 npm，请先安装 Node.js（自带 npm）后重试"
        Pop-Location
        exit 1
    }
    npm install -g swagger2openapi
    $s2o = Get-Command swagger2openapi -ErrorAction SilentlyContinue
}

Write-Host "正在转换为 OpenAPI 3.0 格式..."
if ($null -ne $s2o) {
    swagger2openapi -o $jsonPath -p $jsonPath
} else {
    Write-Host "提示: 全局 bin 目录不在当前 PATH，改用 npx 调用"
    npx -y swagger2openapi -o $jsonPath -p $jsonPath
}

if (-not (Select-String -Path $jsonPath -Pattern '"openapi"\s*:' -Quiet)) {
    Write-Host "错误: 转换后未检测到 openapi 字段，请检查 swagger2openapi 的输出"
    Pop-Location
    exit 1
}
Write-Host "已转换为 OpenAPI 3.0 格式：$jsonPath"

# fix.py：补中文标签、剔除易变字段与 WebSocket 路径，并由 JSON 派生 YAML
$pythonScript = Join-Path $scriptPath "fix.py"
if (($null -eq (Get-Command python3 -ErrorAction SilentlyContinue)) -or (-not (Test-Path $pythonScript))) {
    Write-Host "错误: 未找到可用的 Python 或 fix.py，无法补中文标签并派生 YAML 产物"
    Pop-Location
    exit 1
}

Write-Host "正在处理产物（中文分组、剔除易变字段与 WebSocket 路径、派生 YAML）..."
python3 $pythonScript $jsonPath $yamlPath
if ($LASTEXITCODE -ne 0) {
    Write-Host "错误: fix.py 执行失败"
    Pop-Location
    exit 1
}

Write-Host ""
Write-Host "Swagger文档生成完成！"
Write-Host "JSON文档位置：$jsonPath"
Write-Host "YAML文档位置：$yamlPath"

Pop-Location

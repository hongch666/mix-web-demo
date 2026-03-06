# PowerShell 脚本：生成Swagger文档

# 检查swag是否安装
$swag = Get-Command swag -ErrorAction SilentlyContinue
if ($null -eq $swag) {
    Write-Host "swag未安装，正在安装..."
    go install github.com/swaggo/swag/cmd/swag@latest
}

# 进入app目录
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$appPath = Join-Path $scriptPath "..\..\app"
Push-Location $appPath

Write-Host "正在生成Swagger文档..."
swag init -g internal/handler/routes.go

Write-Host "Swagger文档生成完成！"
Write-Host "文档位置：./docs/"
Write-Host ""
Write-Host "运行以下命令启动服务器："
Write-Host "  go run main.go"
Write-Host ""
Write-Host "然后访问 http://localhost:8082/swagger/index.html"

Pop-Location

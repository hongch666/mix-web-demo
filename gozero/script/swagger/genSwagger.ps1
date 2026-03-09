# PowerShell 脚本：生成Swagger文档 - 使用goctl工具从.api文件生成

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = (Get-Item $scriptPath).Parent.Parent
$apiPath = Join-Path $projectRoot "api"
$appPath = Join-Path $projectRoot "app"

Write-Host "正在验证goctl工具..."
$goctl = Get-Command goctl -ErrorAction SilentlyContinue
if ($null -eq $goctl) {
    Write-Host "错误: goctl未安装"
    Write-Host "请先安装goctl: go install github.com/zeromicro/go-zero/tools/goctl@latest"
    exit 1
}

# 创建输出目录
$docsPath = Join-Path $appPath "docs"
if (-not (Test-Path $docsPath)) {
    New-Item -ItemType Directory -Path $docsPath | Out-Null
}

Write-Host "切换到API目录..."
Push-Location $apiPath

Write-Host "正在生成Swagger文档..."
# 使用goctl从.api文件生成swagger JSON
goctl api swagger --api main.api --dir $docsPath

# 使用goctl生成swagger YAML
goctl api swagger --api main.api --dir $docsPath --yaml

# 检查是否成功生成
if ((Test-Path (Join-Path $docsPath "main.json")) -and (Test-Path (Join-Path $docsPath "main.yaml"))) {
    Write-Host "Swagger文档生成完成！"
    Write-Host "JSON文档位置：./app/docs/main.json"
    Write-Host "YAML文档位置：./app/docs/main.yaml"
    
    # 使用Python脚本为swagger添加中文标签和版本信息
    $pythonScript = Join-Path $scriptPath "add-chinese-tags.py"
    if ((Test-Path $pythonScript) -and ($null -ne (Get-Command python3 -ErrorAction SilentlyContinue))) {
        Write-Host "正在添加中文分组和版本信息..."
        $jsonPath = Join-Path $docsPath "main.json"
        $yamlPath = Join-Path $docsPath "main.yaml"
        python3 $pythonScript $jsonPath $yamlPath
    }
    
    # 清理api目录下可能残留的文件
    Remove-Item -Path "main.json" -Force -ErrorAction SilentlyContinue
    Remove-Item -Path "main.yaml" -Force -ErrorAction SilentlyContinue
    
    Write-Host ""
    Write-Host "可选: 转换为OpenAPI3格式"
    Write-Host "运行: npm install -g swagger2openapi && swagger2openapi -o ../app/docs/main-openapi3.yaml -p ../app/docs/main.json"
} else {
    Write-Host "Swagger文档生成失败"
    Pop-Location
    exit 1
}

Pop-Location

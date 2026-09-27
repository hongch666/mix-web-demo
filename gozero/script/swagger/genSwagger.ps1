# PowerShell 脚本：生成Swagger文档 - 使用goctl工具从.api文件生成
#
# goctl 的输出文件名取自 --api 的文件名（main.api -> main.json / main.yaml），
# 因此这里在生成后统一改名为 openapi.json / openapi.yaml

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = (Get-Item $scriptPath).Parent.Parent
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
# 使用goctl从.api文件生成swagger JSON
goctl api swagger --api main.api --dir $docsPath

# 使用goctl生成swagger YAML
goctl api swagger --api main.api --dir $docsPath --yaml

# goctl 固定输出 main.json / main.yaml，这里按本仓库约定改名
$generatedJson = Join-Path $docsPath "main.json"
$generatedYaml = Join-Path $docsPath "main.yaml"
if (Test-Path $generatedJson) {
    Move-Item -Force $generatedJson $jsonPath
}
if (Test-Path $generatedYaml) {
    Move-Item -Force $generatedYaml $yamlPath
}

# 检查是否成功生成
if ((Test-Path $jsonPath) -and (Test-Path $yamlPath)) {
    Write-Host "Swagger文档生成完成！"
    Write-Host "JSON文档位置：$jsonPath"
    Write-Host "YAML文档位置：$yamlPath"

    # 转换为 OpenAPI 3.0：fix.py 的长连接处理与 servers 清理都按 OpenAPI 3 结构编写，因此这一步必需
    # 未安装时自动安装；装完仍不在 PATH 时退化为 npx 调用
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

    # 使用Python脚本为swagger添加中文标签和版本信息
    $pythonScript = Join-Path $scriptPath "fix.py"
    if ((Test-Path $pythonScript) -and ($null -ne (Get-Command python3 -ErrorAction SilentlyContinue))) {
        Write-Host "正在添加中文分组和版本信息..."
        python3 $pythonScript $jsonPath $yamlPath
    }

    # 清理api目录下可能残留的文件
    Remove-Item -Path "main.json" -Force -ErrorAction SilentlyContinue
    Remove-Item -Path "main.yaml" -Force -ErrorAction SilentlyContinue
} else {
    Write-Host "Swagger文档生成失败"
    Pop-Location
    exit 1
}

Pop-Location

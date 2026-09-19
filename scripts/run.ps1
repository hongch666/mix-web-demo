# 获取脚本所在目录的父目录（项目根目录）
$workdir = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Definition)

# 启动 spring
Start-Process powershell -ArgumentList ". '$workdir/scripts/otel-env.ps1' spring; cd '$workdir/spring'; gradle bootRun"

# 启动 gateway
$gatewayContainer = docker ps -a --format "{{.Names}}" | Where-Object { $_ -eq "mix-gateway" }
if ($gatewayContainer) {
    docker rm -f mix-gateway | Out-Null
}
Push-Location "$workdir/gateway"
docker compose down --remove-orphans | Out-Null
Pop-Location
Start-Process powershell -ArgumentList ". '$workdir/scripts/otel-env.ps1' gateway; cd '$workdir/gateway'; docker compose up"

# 启动 gozero
Start-Process powershell -ArgumentList ". '$workdir/scripts/otel-env.ps1' gozero; cd '$workdir/gozero/app'; fresh"

# 启动 nestjs
Start-Process powershell -ArgumentList ". '$workdir/scripts/otel-env.ps1' nestjs; cd '$workdir/nestjs'; npm run bun:dev"

# 启动 fastapi
Start-Process powershell -ArgumentList ". '$workdir/scripts/otel-env.ps1' fastapi; cd '$workdir/fastapi'; uv run python main.py"

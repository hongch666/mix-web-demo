# 获取脚本所在目录的父目录（项目根目录）
$workdir = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Definition)

# 启动 spring
Start-Process powershell -ArgumentList "cd $workdir/spring; mvn spring-boot:run"

# 启动 gateway
Start-Process powershell -ArgumentList "cd $workdir/gateway; mvn spring-boot:run"

# 启动 gozero
Start-Process powershell -ArgumentList "cd $workdir/gozero; .\gozero_service.exe -f etc/gozero-api.yaml"

# 启动 nestjs
Start-Process powershell -ArgumentList "cd $workdir/nestjs; npm run start"

# 启动 fastapi
Start-Process powershell -ArgumentList "cd $workdir/fastapi; uv run python main.py"

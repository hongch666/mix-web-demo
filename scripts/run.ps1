# 获取脚本所在目录的父目录（项目根目录）
$workdir = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Definition)

# 启动 spring
Start-Process powershell -ArgumentList "cd $workdir/spring; gradle bootRun"

# 启动 gateway
Start-Process powershell -ArgumentList "cd $workdir/gateway; gradle bootRun"

# 启动 gin
Start-Process powershell -ArgumentList "cd $workdir/gin; go run main.go"

# 启动 nestjs
Start-Process powershell -ArgumentList "cd $workdir/nestjs; npm run bun:dev"

# 启动 fastapi
Start-Process powershell -ArgumentList "cd $workdir/fastapi; uv run python main.py"

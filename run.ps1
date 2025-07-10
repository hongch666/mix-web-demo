# 进入脚本所在目录
$workdir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $workdir

# 启动 spring
Start-Process powershell -ArgumentList "cd spring; mvn spring-boot:run"

# 启动 gin
Start-Process powershell -ArgumentList "cd gin; fresh"

# 启动 nestjs
Start-Process powershell -ArgumentList "cd nestjs; npm run start:debug"

# 启动 fastapi
Start-Process powershell -ArgumentList "cd fastapi; venv\Scripts\activate; python -u main.py"

# 启动 gateway
Start-Process powershell -ArgumentList "cd gateway; mvn spring-boot:run"
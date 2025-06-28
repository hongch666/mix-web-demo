#!/bin/bash

SESSION="multi-services"
WORKDIR="$(pwd)"

# 删除旧会话
tmux has-session -t $SESSION 2>/dev/null && tmux kill-session -t $SESSION

# 创建会话并启动第一个窗口：Spring
tmux new-session -d -s $SESSION -n services -c "$WORKDIR"
tmux send-keys -t $SESSION "cd spring && mvn spring-boot:run" C-m

# 水平分屏：Gin
GIN_PANE=$(tmux split-window -h -t $SESSION:0 -c "$WORKDIR")
tmux send-keys -t "$GIN_PANE" "cd gin && fresh" C-m

# 垂直分屏：NestJS（在 Spring 面板下方）
NEST_PANE=$(tmux split-window -v -t $SESSION:0.0 -c "$WORKDIR")
tmux send-keys -t "$NEST_PANE" "cd nestjs && npm run start:debug" C-m

# 垂直分屏：FastAPI（在 Gin 面板下方）
FASTAPI_PANE=$(tmux split-window -v -t "$GIN_PANE" -c "$WORKDIR")
tmux send-keys -t "$FASTAPI_PANE" "cd fastapi && python3 -u main.py" C-m

# 调整为平铺布局，保持清晰
tmux select-layout -t $SESSION:0 tiled

# 设置面板标题（可选）
tmux select-pane -t $SESSION:0.0 -T "1. Spring Boot"
tmux select-pane -t "$GIN_PANE" -T "2. Gin"
tmux select-pane -t "$NEST_PANE" -T "3. NestJS"
tmux select-pane -t "$FASTAPI_PANE" -T "4. FastAPI"

# 创建 Gateway 在另一个窗口（不在当前分屏中）
tmux new-window -t $SESSION -n gateway -c "$WORKDIR"
tmux send-keys -t $SESSION:gateway "cd gateway && mvn spring-boot:run" C-m

# 切回主服务分屏窗口并聚焦 Spring 面板
tmux select-window -t $SESSION:services
tmux select-pane -t $SESSION:services.0

# 附加到 tmux 会话
tmux attach -t $SESSION

#!/bin/bash

SESSION="multi-services"
WORKDIR="$(pwd)"

# 删除旧会话
tmux has-session -t $SESSION 2>/dev/null && tmux kill-session -t $SESSION

# 创建新会话和初始 pane（Spring）
tmux new-session -d -s $SESSION -n services -c "$WORKDIR"
SPRING_PANE=$(tmux display-message -p -t $SESSION:services.0 '#{pane_id}')
tmux send-keys -t "$SPRING_PANE" "cd spring && echo 'Starting Spring Boot...' && mvn spring-boot:run" C-m

# 水平分屏（右上：NestJS）
tmux split-window -h -t "$SPRING_PANE" -c "$WORKDIR"
NEST_PANE=$(tmux display-message -p '#{pane_id}')
tmux send-keys -t "$NEST_PANE" "cd nestjs && echo 'Starting NestJS...' && npm run start:debug" C-m

# 垂直分屏（左下：Gin）
tmux split-window -v -t "$SPRING_PANE" -c "$WORKDIR"
GIN_PANE=$(tmux display-message -p '#{pane_id}')
tmux send-keys -t "$GIN_PANE" "cd gin && echo 'Starting Gin...' && fresh -c ~/.freshrc" C-m

# 垂直分屏（右下：FastAPI）
tmux split-window -v -t "$NEST_PANE" -c "$WORKDIR"
FASTAPI_PANE=$(tmux display-message -p '#{pane_id}')
tmux send-keys -t "$FASTAPI_PANE" "cd fastapi && uv run python main.py" C-m

# 重新调整为平铺布局
tmux select-layout -t $SESSION:services tiled

# 设置面板标题（可选）
tmux select-pane -t "$SPRING_PANE" -T "1. Spring Boot"
tmux select-pane -t "$NEST_PANE" -T "2. NestJS"
tmux select-pane -t "$GIN_PANE" -T "3. Gin"
tmux select-pane -t "$FASTAPI_PANE" -T "4. FastAPI"

# 创建 Gateway 在新窗口
tmux new-window -t $SESSION -n gateway -c "$WORKDIR"
tmux send-keys -t $SESSION:gateway "cd gateway && echo 'Starting Gateway...' && mvn spring-boot:run" C-m

# 切回主服务窗口并聚焦 Spring
tmux select-window -t $SESSION:services
tmux select-pane -t "$SPRING_PANE"

# 附加会话
tmux attach -t $SESSION

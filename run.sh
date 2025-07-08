#!/bin/bash

SESSION="multi-services"
WORKDIR="$(pwd)"

# 创建会话并设置第一个窗口为 spring（编号 1）
tmux new-session -d -s $SESSION -n spring -c "$WORKDIR"
tmux move-window -s $SESSION:0 -t $SESSION:1
tmux send-keys -t $SESSION:1 \
"cd spring && mvn spring-boot:run" C-m

# window 2: gin
tmux new-window -t $SESSION:2 -n gin -c "$WORKDIR"
tmux send-keys -t $SESSION:2 \
"cd gin && fresh" C-m

# window 3: nestjs
tmux new-window -t $SESSION:3 -n nestjs -c "$WORKDIR"
tmux send-keys -t $SESSION:3 \
"cd nestjs && npm run start:debug" C-m

# window 4: fastapi
tmux new-window -t $SESSION:4 -n fastapi -c "$WORKDIR"
tmux send-keys -t $SESSION:4 \
"cd fastapi && source venv/bin/activate && python3 -u main.py" C-m

# window 5: gateway
tmux new-window -t $SESSION:5 -n gateway -c "$WORKDIR"
tmux send-keys -t $SESSION:5 \
"cd gateway && mvn spring-boot:run" C-m

# 选择 spring 窗口并附加
tmux select-window -t $SESSION:1
tmux attach -t $SESSION
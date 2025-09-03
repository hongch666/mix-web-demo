#!/bin/bash

SESSION="multi-services"
WORKDIR="$(pwd)"

# windows 1: spring-article
tmux new-session -d -s $SESSION -n spring-article -c "$WORKDIR"
tmux move-window -s $SESSION:0 -t $SESSION:1
tmux send-keys -t $SESSION:1 \
"cd spring && cd spring-article && mvn spring-boot:run" C-m

# windows 2: spring-user
tmux new-window -t $SESSION:2 -n spring-user -c "$WORKDIR"
tmux send-keys -t $SESSION:2 \
"cd spring && cd spring-user && mvn spring-boot:run" C-m

# windows 3: spring-category
tmux new-window -t $SESSION:3 -n spring-category -c "$WORKDIR"
tmux send-keys -t $SESSION:3 \
"cd spring && cd spring-category && mvn spring-boot:run" C-m

# windows 4: spring-gateway
tmux new-window -t $SESSION:4 -n spring-gateway -c "$WORKDIR"
tmux send-keys -t $SESSION:4 \
"cd spring && cd spring-gateway && mvn spring-boot:run" C-m

# windows 5: gin-chat
tmux new-window -t $SESSION:5 -n gin-chat -c "$WORKDIR"
tmux send-keys -t $SESSION:5 \
"cd gin && cd gin-chat && fresh" C-m

# windows 6: gin-search
tmux new-window -t $SESSION:6 -n gin-search -c "$WORKDIR"
tmux send-keys -t $SESSION:6 \
"cd gin && cd gin-search && fresh" C-m

# windows 7: nestjs-logs
tmux new-window -t $SESSION:7 -n nestjs-logs -c "$WORKDIR"
tmux send-keys -t $SESSION:7 \
"cd nestjs && cd nestjs-logs && npm run start:debug" C-m

# windows 8: nestjs-download
tmux new-window -t $SESSION:8 -n nestjs-download -c "$WORKDIR"
tmux send-keys -t $SESSION:8 \
"cd nestjs && cd nestjs-download && npm run start:download" C-m

# windows 9: fastapi-data
tmux new-window -t $SESSION:9 -n fastapi-data -c "$WORKDIR"
tmux send-keys -t $SESSION:9 \
"cd fastapi && cd fastapi-data && source venv/bin/activate && python3 -u main.py" C-m

# windows 10: fastapi-ai
tmux new-window -t $SESSION:10 -n fastapi-ai -c "$WORKDIR"
tmux send-keys -t $SESSION:10 \
"cd fastapi && cd fastapi-ai && source venv/bin/activate && python3 -u main.py" C-m

# 选择 spring 窗口并附加
tmux select-window -t $SESSION:1
tmux attach -t $SESSION
#!/bin/bash

SESSION="multi-services"

# 创建会话并设置第一个窗口为 spring（编号 1）
tmux new-session -d -s $SESSION -n spring
tmux move-window -s $SESSION:0 -t $SESSION:1
tmux send-keys -t $SESSION:1 \
'/usr/bin/env /usr/lib/jvm/java-17-openjdk-amd64/bin/java @/tmp/cp_61utw0k2kzdf2tu6oe18bensk.argfile com.hcsy.spring.Application' C-m

# window 2: gin
tmux new-window -t $SESSION:2 -n gin
tmux send-keys -t $SESSION:2 \
'cd "/home/hongch666/桌面/code/mix-web-demo/gin/" && fresh' C-m

# window 3: nestjs
tmux new-window -t $SESSION:3 -n nestjs
tmux send-keys -t $SESSION:3 \
'cd ~/桌面/code/mix-web-demo/nestjs && npm run start:debug' C-m

# window 4: fastapi
tmux new-window -t $SESSION:4 -n fastapi
tmux send-keys -t $SESSION:4 \
'cd "/home/hongch666/桌面/code/mix-web-demo/fastapi/" && python3 -u main.py' C-m

# window 5: gateway
tmux new-window -t $SESSION:5 -n gateway
tmux send-keys -t $SESSION:5 \
'/usr/bin/env /usr/lib/jvm/java-17-openjdk-amd64/bin/java @/tmp/cp_bjcg176c0z8weqaoerbbjz8od.argfile com.hcsy.gateway.GatewayApplication' C-m

# 选择 spring 窗口并附加
tmux select-window -t $SESSION:1
tmux attach -t $SESSION

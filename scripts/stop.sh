#!/bin/bash

tmux kill-session -t multi-services 2>/dev/null || true

if command -v docker >/dev/null 2>&1; then
    docker stop mix-gateway >/dev/null 2>&1 || true
fi

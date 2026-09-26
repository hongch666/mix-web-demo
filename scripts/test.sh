#!/bin/bash

WORKDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [ $# -gt 0 ]; then
    SERVICES="$*"
else
    SERVICES="spring gozero nestjs fastapi"
fi

run_spring_tests() {
    command -v mvn >/dev/null 2>&1 || return 2
    (cd "$WORKDIR/spring" && mvn test)
}

run_gozero_tests() {
    command -v go >/dev/null 2>&1 || return 2
    (cd "$WORKDIR/gozero/app" && go test ./... -count=1)
}

run_nestjs_tests() {
    if command -v bun >/dev/null 2>&1; then
        (cd "$WORKDIR/nestjs" && bun test)
        return
    fi
    command -v npm >/dev/null 2>&1 || return 2
    (cd "$WORKDIR/nestjs" && npm test -- --runInBand)
}

run_fastapi_tests() {
    export PYTHONPATH="$WORKDIR/fastapi${PYTHONPATH:+:$PYTHONPATH}"
    if command -v uv >/dev/null 2>&1; then
        (cd "$WORKDIR/fastapi" && uv run pytest)
        return
    fi
    if command -v pytest >/dev/null 2>&1; then
        (cd "$WORKDIR/fastapi" && pytest)
        return
    fi
    if [ -x "$WORKDIR/fastapi/.venv/bin/pytest" ]; then
        (cd "$WORKDIR/fastapi" && .venv/bin/pytest)
        return
    fi
    if [ -x "$WORKDIR/fastapi/.venv/Scripts/pytest.exe" ]; then
        (cd "$WORKDIR/fastapi" && .venv/Scripts/pytest.exe)
        return
    fi
    return 2
}

FAILED_SERVICES=""

for SERVICE in $SERVICES; do
    echo ""
    case "$SERVICE" in
        spring) run_spring_tests; STATUS=$? ;;
        gozero) run_gozero_tests; STATUS=$? ;;
        nestjs) run_nestjs_tests; STATUS=$? ;;
        fastapi) run_fastapi_tests; STATUS=$? ;;
        gateway)
            echo "Skipping gateway: no unit test command."
            continue
            ;;
        *)
            echo "Unknown service: $SERVICE"
            echo "Available services: spring gozero nestjs fastapi"
            exit 1
            ;;
    esac

    case $STATUS in
        0) echo "Tests passed: $SERVICE" ;;
        2) echo "Tests skipped: $SERVICE (required tool not installed)" ;;
        *)
            echo "Tests failed: $SERVICE"
            FAILED_SERVICES="$FAILED_SERVICES $SERVICE"
            ;;
    esac
done

if [ -n "$FAILED_SERVICES" ]; then
    echo "Failed services:$FAILED_SERVICES"
    exit 1
fi

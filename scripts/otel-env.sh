#!/bin/bash

OTEL_SERVICE_NAME_ARG=${1:-}
OTEL_PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [ -z "${OTEL_ENABLED+x}" ]; then
    if [ -f "$OTEL_PROJECT_ROOT/.otel/enabled" ]; then
        export OTEL_ENABLED=true
    else
        export OTEL_ENABLED=false
    fi
fi
export OTEL_SERVICE_NAME="${OTEL_SERVICE_NAME:-$OTEL_SERVICE_NAME_ARG}"
export OTEL_TRACES_SAMPLER="${OTEL_TRACES_SAMPLER:-always_on}"

if [ "$OTEL_SERVICE_NAME_ARG" = "gateway" ]; then
    export APISIX_OTEL_ENABLED="$OTEL_ENABLED"
fi

if [ "$OTEL_SERVICE_NAME_ARG" = "gozero" ]; then
    export OTEL_DISABLED="$([ "$OTEL_ENABLED" = "true" ] && echo false || echo true)"
    export OTEL_EXPORTER_OTLP_ENDPOINT="${OTEL_EXPORTER_OTLP_ENDPOINT:-127.0.0.1:4318}"
    export OTEL_TRACES_SAMPLER_RATIO="${OTEL_TRACES_SAMPLER_RATIO:-1.0}"
else
    export OTEL_EXPORTER_OTLP_ENDPOINT="${OTEL_EXPORTER_OTLP_ENDPOINT:-http://127.0.0.1:4318}"
    export OTEL_EXPORTER_OTLP_TRACES_ENDPOINT="${OTEL_EXPORTER_OTLP_TRACES_ENDPOINT:-${OTEL_EXPORTER_OTLP_ENDPOINT%/}/v1/traces}"
fi

if [ "$OTEL_SERVICE_NAME_ARG" = "spring" ] && [ "$OTEL_ENABLED" = "true" ]; then
    OTEL_JAVA_AGENT_VERSION="${OTEL_JAVA_AGENT_VERSION:-2.31.1}"
    OTEL_JAVA_AGENT_DIR="$OTEL_PROJECT_ROOT/.otel"
    OTEL_JAVA_AGENT_PATH="$OTEL_JAVA_AGENT_DIR/opentelemetry-javaagent.jar"

    if [ ! -s "$OTEL_JAVA_AGENT_PATH" ]; then
        mkdir -p "$OTEL_JAVA_AGENT_DIR"
        OTEL_JAVA_AGENT_TMP="$OTEL_JAVA_AGENT_PATH.tmp"
        if ! curl -fsSL --connect-timeout 10 --max-time 300 --retry 3 --retry-all-errors \
            "https://maven.aliyun.com/repository/public/io/opentelemetry/javaagent/opentelemetry-javaagent/${OTEL_JAVA_AGENT_VERSION}/opentelemetry-javaagent-${OTEL_JAVA_AGENT_VERSION}.jar" \
            -o "$OTEL_JAVA_AGENT_TMP"; then
            rm -f "$OTEL_JAVA_AGENT_TMP"
            echo "警告: OpenTelemetry Java Agent 下载失败，本次 Spring 启动不启用追踪" >&2
            export OTEL_ENABLED=false
            return 0 2>/dev/null || exit 0
        fi
        mv "$OTEL_JAVA_AGENT_TMP" "$OTEL_JAVA_AGENT_PATH"
    fi

    case " ${JAVA_TOOL_OPTIONS:-} " in
        *" -javaagent:$OTEL_JAVA_AGENT_PATH "*) ;;
        *) export JAVA_TOOL_OPTIONS="${JAVA_TOOL_OPTIONS:+$JAVA_TOOL_OPTIONS }-javaagent:$OTEL_JAVA_AGENT_PATH" ;;
    esac
fi

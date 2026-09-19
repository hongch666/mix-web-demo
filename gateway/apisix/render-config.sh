#!/bin/sh

set -eu

case "${APISIX_OTEL_ENABLED:-false}" in
    true)
        otel_sampler="always_on"
        ;;
    false)
        otel_sampler="always_off"
        ;;
    *)
        echo "APISIX_OTEL_ENABLED 仅支持 true 或 false" >&2
        exit 1
        ;;
esac

sed "s/__APISIX_OTEL_SAMPLER__/$otel_sampler/" \
    /usr/local/apisix/conf/apisix.yaml.template \
    > /usr/local/apisix/conf/apisix.yaml

exec /docker-entrypoint.sh docker-start

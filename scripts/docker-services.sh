#!/bin/bash

# Docker 容器管理脚本
# 用于创建和管理项目所需的 Docker 容器
# 账号密码支持在项目根目录 .env 中自定义（参考根目录 .env.example），未配置时使用内置默认值

set -e

# 项目根目录（脚本位于 <root>/scripts/ 下），.env 与 nacos/custom.env 均以根目录为基准
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="$PROJECT_ROOT/.env"
cd "$PROJECT_ROOT"

# 是否加载到根目录 .env，用于后续默认密码提示
ENV_LOADED=false

# 加载环境变量
if [ -f "$ENV_FILE" ]; then
    set -a
    . "$ENV_FILE"
    set +a
    ENV_LOADED=true
fi

# 默认账号密码配置（优先使用 .env 中的变量）
# DB_PASSWORD 为兼容旧配置的公共回退值，MySQL 与 PostgreSQL 建议分别使用独立变量
DB_PASSWORD=${DB_PASSWORD:-123456}
MYSQL_ROOT_PASSWORD=${MYSQL_ROOT_PASSWORD:-$DB_PASSWORD}
POSTGRES_USER=${POSTGRES_USER:-postgres}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-$DB_PASSWORD}
REDIS_PASSWORD=${REDIS_PASSWORD:-123456}
# ES 版本：镜像与 IK 分词器插件版本必须一致
ES_VERSION=${ES_VERSION:-7.12.1}
# 是否自动安装 IK 分词器（GoZero 文章搜索刚需，默认开启）
ES_IK_ENABLED=${ES_IK_ENABLED:-true}
# 是否强制使用离线插件包：true 时只用 ES_IK_OFFLINE_ZIP，不再尝试在线地址
ES_IK_OFFLINE=${ES_IK_OFFLINE:-false}
# 离线插件包在宿主机上的绝对路径（配置且文件存在时优先使用）
ES_IK_OFFLINE_ZIP=${ES_IK_OFFLINE_ZIP:-}
ES_SECURITY_ENABLED=${ES_SECURITY_ENABLED:-true}
ES_PASSWORD=${ES_PASSWORD:-123456}
ES_HEAP_SIZE=${ES_HEAP_SIZE:-256m}
MONGO_USER=${MONGO_USER:-root}
MONGO_PASSWORD=${MONGO_PASSWORD:-123456}
CLICKHOUSE_USER=${CLICKHOUSE_USER:-hcsy}
CLICKHOUSE_PASSWORD=${CLICKHOUSE_PASSWORD:-123456}
RABBITMQ_USER=${RABBITMQ_USER:-hcsy}
RABBITMQ_PASSWORD=${RABBITMQ_PASSWORD:-123456}
NEO4J_USER=${NEO4J_USER:-neo4j}
NEO4J_PASSWORD=${NEO4J_PASSWORD:-12345678}

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_debug() {
    echo -e "${BLUE}[DEBUG]${NC} $1"
}

# 判断 ElasticSearch 是否开启安全认证，兼容 true/1/yes/on（忽略大小写）
es_security_on() {
    case "$(printf '%s' "$ES_SECURITY_ENABLED" | tr '[:upper:]' '[:lower:]')" in
        true|1|yes|on)
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}

# 校验账号密码来源，并提示仍在使用内置默认值的项
check_credentials() {
    if [ "$ENV_LOADED" = true ]; then
        log_info "已加载环境变量文件: $ENV_FILE"
    else
        log_warn "未找到 $ENV_FILE，将使用内置默认账号密码"
        log_warn "生产环境请先复制根目录 .env.example 为 .env 并修改密码"
    fi

    local weak_credentials=()

    if [ "$MYSQL_ROOT_PASSWORD" = "123456" ]; then
        weak_credentials+=("MYSQL_ROOT_PASSWORD")
    fi
    if [ "$POSTGRES_PASSWORD" = "123456" ]; then
        weak_credentials+=("POSTGRES_PASSWORD")
    fi
    if es_security_on && [ "$ES_PASSWORD" = "123456" ]; then
        weak_credentials+=("ES_PASSWORD")
    fi
    if [ "$REDIS_PASSWORD" = "123456" ]; then
        weak_credentials+=("REDIS_PASSWORD")
    fi
    if [ "$MONGO_PASSWORD" = "123456" ]; then
        weak_credentials+=("MONGO_PASSWORD")
    fi
    if [ "$CLICKHOUSE_PASSWORD" = "123456" ]; then
        weak_credentials+=("CLICKHOUSE_PASSWORD")
    fi
    if [ "$RABBITMQ_PASSWORD" = "123456" ]; then
        weak_credentials+=("RABBITMQ_PASSWORD")
    fi
    if [ "$NEO4J_PASSWORD" = "12345678" ]; then
        weak_credentials+=("NEO4J_PASSWORD")
    fi

    if [ ${#weak_credentials[@]} -ne 0 ]; then
        log_warn "以下账号密码仍为默认值，建议在生产环境修改:"
        for item in "${weak_credentials[@]}"; do
            echo "    - $item"
        done
    fi
}

# 检查 Docker 是否安装
check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安装"
        echo ""
        echo "请根据系统类型安装 Docker:"
        echo "1. Linux (Ubuntu/Debian):"
        echo "   curl -fsSL https://get.docker.com -o get-docker.sh && sudo sh get-docker.sh"
        echo ""
        echo "2. Linux (CentOS):"
        echo "   sudo yum install -y docker-io"
        echo ""
        echo "3. macOS:"
        echo "   brew install docker 或下载 Docker Desktop"
        echo ""
        echo "4. Windows:"
        echo "   下载 Docker Desktop for Windows"
        echo ""
        exit 1
    fi
    log_info "Docker 已安装: $(docker --version)"
}

# 检查 Docker 服务是否运行
check_docker_daemon() {
    if ! docker ps &> /dev/null; then
        log_error "Docker 守护进程未运行"
        echo "请启动 Docker 服务:"
        echo "  Linux: sudo systemctl start docker"
        echo "  macOS/Windows: 打开 Docker Desktop"
        exit 1
    fi
    log_info "Docker 守护进程运行正常"
}

# 检查端口是否被占用
check_port() {
    local port=$1
    local service=$2

    if netstat -tuln 2>/dev/null | grep -q ":$port " || ss -tuln 2>/dev/null | grep -q ":$port "; then
        log_warn "$service 的端口 $port 已被占用，容器已存在，跳过创建"
        log_warn "如需应用 .env 中的新账号密码，请先执行 ./mix docker-services delete 后再 up"
        return 0
    fi
    return 1
}

# 获取已运行的容器
get_running_containers() {
    docker ps --format '{{.Names}}' 2>/dev/null || echo ""
}

# 创建 Docker 网络
create_docker_network() {
    local network=$1

    if docker network inspect "$network" &>/dev/null; then
        log_info "Docker 网络 '$network' 已存在"
        return 0
    fi

    log_info "创建 Docker 网络: $network"
    docker network create "$network" 2>/dev/null || true
}

# 创建容器前的准备
prepare_directories() {
    log_info "准备数据目录..."

    mkdir -p ~/mysql/data ~/mysql/conf ~/mysql/init
    mkdir -p ~/pgdata
    mkdir -p ~/redis_data
    mkdir -p ~/mongo_data
    mkdir -p ~/clickhouse/data ~/clickhouse/logs
    mkdir -p ~/neo4j/data ~/neo4j/logs ~/neo4j/conf ~/neo4j/import

    log_info "数据目录准备完成"
}

# MySQL 容器
create_mysql() {
    log_info "创建 MySQL 容器..."

    if check_port 3306 "MySQL"; then
        return 0
    fi

    docker run -d \
        --name mysql \
        -p 3306:3306 \
        -e TZ=Asia/Shanghai \
        -e MYSQL_ROOT_PASSWORD="$MYSQL_ROOT_PASSWORD" \
        -v ~/mysql/data:/var/lib/mysql \
        -v ~/mysql/conf:/etc/mysql/conf.d \
        -v ~/mysql/init:/docker-entrypoint-initdb.d \
        --network hcsy \
        --restart=always \
        mysql

    log_info "MySQL 容器创建成功 (端口 3306)"
}

# PostgreSQL 容器
create_postgresql() {
    log_info "创建 PostgreSQL 容器..."

    if check_port 5432 "PostgreSQL"; then
        return 0
    fi

    docker run -d \
        --name pgvector-db \
        -e POSTGRES_USER="$POSTGRES_USER" \
        -e POSTGRES_PASSWORD="$POSTGRES_PASSWORD" \
        -e POSTGRES_DB=testdb \
        -p 5432:5432 \
        -v ~/pgdata:/var/lib/postgresql/data \
        --network hcsy \
        --restart=always \
        ankane/pgvector:latest

    log_info "PostgreSQL 容器创建成功 (端口 5432)"
}

# Redis 容器
create_redis() {
    log_info "创建 Redis 容器..."

    if check_port 6379 "Redis"; then
        return 0
    fi

    docker run -d \
        --name redis \
        -p 6379:6379 \
        -v ~/redis_data:/data \
        --network hcsy \
        --restart=always \
        redis:7 redis-server --appendonly yes --requirepass "$REDIS_PASSWORD"

    log_info "Redis 容器创建成功 (端口 6379)"
}

# MongoDB 容器
create_mongodb() {
    log_info "创建 MongoDB 容器..."

    if check_port 27017 "MongoDB"; then
        return 0
    fi

    docker run -d \
        --name mongodb \
        -p 27017:27017 \
        -e MONGO_INITDB_ROOT_USERNAME="$MONGO_USER" \
        -e MONGO_INITDB_ROOT_PASSWORD="$MONGO_PASSWORD" \
        -v ~/mongo_data:/data/db \
        --network hcsy \
        --restart=always \
        mongo:6

    log_info "MongoDB 容器创建成功 (端口 27017)"
}

# ElasticSearch IK 插件下载地址（按顺序尝试，任一成功即可）
ES_IK_PLUGIN_URLS="
https://release.infinilabs.com/analysis-ik/stable/elasticsearch-analysis-ik-${ES_VERSION}.zip
https://get.infini.cloud/elasticsearch/analysis-ik/${ES_VERSION}
"

# 判断是否自动安装 IK 分词器，兼容 true/1/yes/on（忽略大小写）
es_ik_on() {
    case "$(printf '%s' "$ES_IK_ENABLED" | tr '[:upper:]' '[:lower:]')" in
        true|1|yes|on)
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}

# 判断 IK 分词器插件是否已安装（插件存放在 es-plugins 共享卷中）
es_plugin_installed() {
    docker run --rm \
        -v es-plugins:/usr/share/elasticsearch/plugins \
        --entrypoint /bin/sh \
        "elasticsearch:${ES_VERSION}" \
        -c 'test -d /usr/share/elasticsearch/plugins/analysis-ik' >/dev/null 2>&1
}

# 判断是否强制使用离线插件包，兼容 true/1/yes/on（忽略大小写）
es_ik_offline_on() {
    case "$(printf '%s' "$ES_IK_OFFLINE" | tr '[:upper:]' '[:lower:]')" in
        true|1|yes|on)
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}

# 使用宿主机上的离线 zip 安装 IK 插件，参数为安装方式: offline(容器启动前) / online(运行中的容器)
install_es_ik_plugin_from_zip() {
    local mode=${1:-offline}
    # 容器内的固定挂载路径，与宿主机上的文件名无关
    local container_zip="/tmp/analysis-ik.zip"

    if [ ! -f "$ES_IK_OFFLINE_ZIP" ]; then
        log_error "离线插件包不存在: $ES_IK_OFFLINE_ZIP"
        return 1
    fi

    log_info "使用离线插件包安装 IK 分词器: $ES_IK_OFFLINE_ZIP"

    if [ "$mode" = "offline" ]; then
        # 以 root 运行临时容器写入插件卷，避免权限问题；启动前完成安装可免重启
        if docker run --rm \
            --user 0:0 \
            -v es-plugins:/usr/share/elasticsearch/plugins \
            -v "$ES_IK_OFFLINE_ZIP:$container_zip:ro" \
            -e ES_HOME=/usr/share/elasticsearch \
            --entrypoint /usr/share/elasticsearch/bin/elasticsearch-plugin \
            "elasticsearch:${ES_VERSION}" \
            install --batch "file://$container_zip"; then
            log_info "IK 分词器插件安装成功（离线包）"
            return 0
        fi
    else
        # 运行中的容器：先拷入 zip，再通过 file:// 安装，最后清理临时文件
        if docker cp "$ES_IK_OFFLINE_ZIP" "es:$container_zip" &&
            docker exec -u 0:0 es \
                /usr/share/elasticsearch/bin/elasticsearch-plugin install --batch "file://$container_zip"; then
            docker exec es rm -f "$container_zip" >/dev/null 2>&1 || true
            log_info "重启 ElasticSearch 容器以加载插件..."
            docker restart es >/dev/null
            log_info "IK 分词器插件安装成功（离线包）"
            return 0
        fi
        docker exec es rm -f "$container_zip" >/dev/null 2>&1 || true
    fi

    log_error "离线插件包安装失败: $ES_IK_OFFLINE_ZIP"
    return 1
}

# 安装 IK 分词器插件，参数为安装方式: offline(容器启动前装入共享卷) / online(运行中的容器)
# 离线优先规则：ES_IK_OFFLINE=true 时只用离线包；否则配置了 ES_IK_OFFLINE_ZIP 且文件存在时优先离线，失败再走在线地址
# 注意：插件版本必须与 ES 版本一致，否则 ES 启动会校验失败
install_es_ik_plugin() {
    local mode=${1:-offline}
    local url
    local installed=false

    if es_ik_offline_on; then
        if [ -z "$ES_IK_OFFLINE_ZIP" ]; then
            log_error "ES_IK_OFFLINE=true 但未配置 ES_IK_OFFLINE_ZIP（离线插件包路径）"
            return 1
        fi
        install_es_ik_plugin_from_zip "$mode" || return 1
        return 0
    fi

    if [ -n "$ES_IK_OFFLINE_ZIP" ] && [ -f "$ES_IK_OFFLINE_ZIP" ]; then
        if install_es_ik_plugin_from_zip "$mode"; then
            return 0
        fi
        log_warn "离线包安装失败，改为尝试在线下载"
    fi

    for url in $ES_IK_PLUGIN_URLS; do
        log_info "尝试安装 IK 分词器插件: $url"
        if [ "$mode" = "offline" ]; then
            # 以 root 运行临时容器写入插件卷，避免权限问题；启动前完成安装可免重启
            if docker run --rm \
                --user 0:0 \
                -v es-plugins:/usr/share/elasticsearch/plugins \
                -e ES_HOME=/usr/share/elasticsearch \
                --entrypoint /usr/share/elasticsearch/bin/elasticsearch-plugin \
                "elasticsearch:${ES_VERSION}" \
                install --batch "$url"; then
                installed=true
            fi
        else
            if docker exec -u 0:0 es \
                /usr/share/elasticsearch/bin/elasticsearch-plugin install --batch "$url"; then
                log_info "重启 ElasticSearch 容器以加载插件..."
                docker restart es >/dev/null
                installed=true
            fi
        fi

        if [ "$installed" = true ]; then
            log_info "IK 分词器插件安装成功"
            return 0
        fi
        log_warn "该地址安装失败，尝试下一个下载地址"
    done

    log_error "IK 分词器插件安装失败，文章搜索功能将不可用"
    log_error "可在根目录 .env 中配置 ES_IK_OFFLINE_ZIP 指向本地插件包后重试，或手动执行（版本需与 ES 一致: $ES_VERSION）:"
    echo "  docker run --rm --user 0:0 -v es-plugins:/usr/share/elasticsearch/plugins \\"
    echo "      --entrypoint /usr/share/elasticsearch/bin/elasticsearch-plugin \\"
    echo "      elasticsearch:${ES_VERSION} install --batch https://release.infinilabs.com/analysis-ik/stable/elasticsearch-analysis-ik-${ES_VERSION}.zip"
    return 1
}

# 在 ES 容器内探测 URL 的 HTTP 状态码，探测失败返回 000
es_http_code() {
    local auth_args=$1
    local url=$2
    local code=""

    if docker exec es sh -c 'command -v curl >/dev/null 2>&1'; then
        code=$(docker exec es curl -s -m 3 -o /dev/null -w '%{http_code}' $auth_args "$url" 2>/dev/null || true)
    elif docker exec es sh -c 'command -v wget >/dev/null 2>&1'; then
        code=$(docker exec es sh -c "wget -q -S -O /dev/null $auth_args '$url' 2>&1" \
            | awk 'NR==1 {print $2}' 2>/dev/null || true)
    fi

    echo "${code:-000}"
}

# 等待 ElasticSearch 就绪（最多约 150 秒）
wait_es_ready() {
    local auth_args=""
    if es_security_on; then
        auth_args="-u elastic:$ES_PASSWORD"
    fi

    local i code
    for i in $(seq 1 30); do
        code=$(es_http_code "$auth_args" "http://localhost:9200/")
        if [ "$code" = "200" ]; then
            return 0
        fi
        sleep 5
    done

    log_error "ElasticSearch 启动超时，请查看容器日志: docker logs es"
    return 1
}

# 验证 IK 分词器可用（GoZero 文章搜索使用 ik_smart 分词，属于刚需）
verify_es_ik() {
    local auth_args=""
    if es_security_on; then
        auth_args="-u elastic:$ES_PASSWORD"
    fi

    local resp
    resp=$(docker exec es sh -c "curl -s -m 5 $auth_args -H 'Content-Type: application/json' -X POST 'http://localhost:9200/_analyze' -d '{\"analyzer\":\"ik_smart\",\"text\":\"中华人民共和国国歌\"}'" 2>/dev/null || true)

    if printf '%s' "$resp" | grep -q '"token"'; then
        log_info "IK 分词器验证通过（ik_smart 分词正常）"
        return 0
    fi

    log_error "IK 分词器验证失败，响应: ${resp:-空}"
    return 1
}

# ElasticSearch 容器
create_elasticsearch() {
    log_info "创建 ElasticSearch 容器..."

    if check_port 9200 "ElasticSearch"; then
        # 容器已存在时同样确保 IK 插件可用（本次改造前创建的容器可能未装插件）
        if es_ik_on && ! es_plugin_installed; then
            if install_es_ik_plugin online; then
                if wait_es_ready; then
                    verify_es_ik || log_warn "IK 分词器未验证通过，请检查上方日志"
                fi
            fi
        else
            log_info "ElasticSearch 容器已存在，IK 分词器插件已就绪"
        fi
        return 0
    fi

    # 开启安全认证时，通过 ELASTIC_PASSWORD 设置内置 elastic 用户的密码
    local security_opts=()
    if es_security_on; then
        security_opts=(
            -e "xpack.security.enabled=true"
            -e "ELASTIC_PASSWORD=$ES_PASSWORD"
        )
    fi

    # IK 分词器在容器启动前装入共享插件卷，ES 首次启动即可加载，无需重启
    if es_ik_on; then
        if es_plugin_installed; then
            log_info "IK 分词器插件已安装，跳过"
        else
            install_es_ik_plugin offline || true
        fi
    fi

    docker run -d \
        --name es \
        -e "ES_JAVA_OPTS=-Xms$ES_HEAP_SIZE -Xmx$ES_HEAP_SIZE" \
        -e "discovery.type=single-node" \
        "${security_opts[@]}" \
        -v es-data:/usr/share/elasticsearch/data \
        -v es-plugins:/usr/share/elasticsearch/plugins \
        --privileged \
        --network hcsy \
        --restart=always \
        -p 9200:9200 \
        -p 9300:9300 \
        "elasticsearch:${ES_VERSION}"

    log_info "ElasticSearch 容器创建成功 (端口 9200, 9300)"

    # 等待就绪并验证 IK 分词器
    log_info "等待 ElasticSearch 启动..."
    if wait_es_ready; then
        log_info "ElasticSearch 已就绪"
        if es_ik_on; then
            if ! verify_es_ik; then
                log_warn "IK 分词器未验证通过，文章搜索可能不可用，请检查上方日志"
            fi
        fi
    fi
}

# 生成 Nacos 环境变量文件，MySQL 密码与 DB_PASSWORD 保持同步
# 注意：docker --env-file 不做变量替换，此处必须写入真实密码，不能写 ${DB_PASSWORD}
generate_nacos_env() {
    local nacos_dir="$PROJECT_ROOT/nacos"
    local target="$nacos_dir/custom.env"
    local tmp="$target.tmp"

    mkdir -p "$nacos_dir"

    cat > "$tmp" << EOF
MODE=standalone
NACOS_AUTH_ENABLE=false
SPRING_DATASOURCE_PLATFORM=mysql
MYSQL_SERVICE_HOST=mysql
MYSQL_SERVICE_PORT=3306
MYSQL_SERVICE_USER=root
MYSQL_SERVICE_PASSWORD=$MYSQL_ROOT_PASSWORD
MYSQL_SERVICE_DB_NAME=nacos
EOF

    # 内容无变化时保留原文件，避免每次 up 都产生变更
    if [ -f "$target" ] && [ "$(cat "$target")" = "$(cat "$tmp")" ]; then
        rm -f "$tmp"
        return 0
    fi

    mv "$tmp" "$target"
    log_info "已生成 nacos/custom.env（MySQL 密码与 DB_PASSWORD 同步）"
}

# Nacos 容器
create_nacos() {
    log_info "创建 Nacos 容器..."

    if check_port 8848 "Nacos"; then
        return 0
    fi

    generate_nacos_env

    docker run -d \
        --name nacos \
        --env-file "$PROJECT_ROOT/nacos/custom.env" \
        -p 8848:8848 \
        -p 9848:9848 \
        -p 9849:9849 \
        --network hcsy \
        --restart=always \
        nacos/nacos-server:v2.1.0-slim

    log_info "Nacos 容器创建成功 (端口 8848, 9848, 9849)"
}

# RabbitMQ 容器
create_rabbitmq() {
    log_info "创建 RabbitMQ 容器..."

    if check_port 5672 "RabbitMQ"; then
        return 0
    fi

    docker run \
        -e RABBITMQ_DEFAULT_USER="$RABBITMQ_USER" \
        -e RABBITMQ_DEFAULT_PASS="$RABBITMQ_PASSWORD" \
        -v mq-plugins:/plugins \
        --name mq \
        --hostname mq \
        -p 15672:15672 \
        -p 5672:5672 \
        --network hcsy \
        --restart=always \
        -d \
        rabbitmq:3.8-management

    log_info "RabbitMQ 容器创建成功 (端口 5672, 15672)"
}

# ClickHouse 容器
create_clickhouse() {
    log_info "创建 ClickHouse 容器..."

    if check_port 8123 "ClickHouse"; then
        return 0
    fi

    docker run -d \
        --name clickhouse \
        --restart always \
        --network hcsy \
        -p 8123:8123 \
        -p 9002:9000 \
        -e CLICKHOUSE_USER="$CLICKHOUSE_USER" \
        -e CLICKHOUSE_PASSWORD="$CLICKHOUSE_PASSWORD" \
        -v ~/clickhouse/data:/var/lib/clickhouse \
        -v ~/clickhouse/logs:/var/log/clickhouse-server \
        --ulimit nofile=262144:262144 \
        clickhouse/clickhouse-server

    log_info "ClickHouse 容器创建成功 (端口 8123, 9002)"
}

# Neo4j 容器
create_neo4j() {
    log_info "创建 Neo4j 容器..."

    if check_port 7687 "Neo4j"; then
        return 0
    fi
    if check_port 7474 "Neo4j Browser"; then
        return 0
    fi

    docker run -d \
        --name neo4j \
        --restart always \
        --network hcsy \
        -p 7474:7474 \
        -p 7687:7687 \
        -v "$HOME/neo4j/data":/data \
        -v "$HOME/neo4j/logs":/logs \
        -v "$HOME/neo4j/conf":/conf \
        -v "$HOME/neo4j/import":/import \
        -e NEO4J_AUTH="$NEO4J_USER/$NEO4J_PASSWORD" \
        neo4j

    log_info "Neo4j 容器创建成功 (端口 7474, 7687)"
}

# 显示所有容器状态
show_status() {
    echo ""
    log_info "容器状态:"
    echo ""
    docker ps --format 'table {{.Names}}\t{{.Ports}}\t{{.Status}}' | grep -E "mysql|pgvector|redis|mongodb|es|nacos|mq|clickhouse|neo4j" || echo "没有相关容器运行"
    echo ""
}

# 停止所有容器
stop_all() {
    log_warn "停止所有容器..."

    for container in mysql pgvector-db redis mongodb es nacos mq clickhouse neo4j; do
        if docker ps -a --format '{{.Names}}' | grep -q "^${container}$"; then
            log_info "停止 $container..."
            docker stop "$container" 2>/dev/null || true
        fi
    done

    log_info "所有容器已停止"
}

# 删除所有容器
delete_all() {
    log_error "删除所有容器..."

    read -p "确认删除所有容器? (y/n): " confirm
    if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
        log_warn "已取消删除操作"
        return 0
    fi

    for container in mysql pgvector-db redis mongodb es nacos mq clickhouse neo4j; do
        if docker ps -a --format '{{.Names}}' | grep -q "^${container}$"; then
            log_info "删除 $container..."
            docker stop "$container" 2>/dev/null || true
            docker rm "$container" 2>/dev/null || true
        fi
    done

    log_info "所有容器已删除"
}

# 显示日志
show_logs() {
    local service=$1

    if [ -z "$service" ]; then
        log_error "请指定服务名称"
        echo "可用服务: mysql, postgresql, redis, mongodb, elasticsearch, nacos, rabbitmq, neo4j"
        return 1
    fi

    case $service in
        mysql)
            docker logs -f mysql
            ;;
        postgresql|postgres)
            docker logs -f pgvector-db
            ;;
        redis)
            docker logs -f redis
            ;;
        mongodb|mongo)
            docker logs -f mongodb
            ;;
        elasticsearch|es)
            docker logs -f es
            ;;
        clickhouse)
            docker logs -f clickhouse
            ;;
        nacos)
            docker logs -f nacos
            ;;
        rabbitmq|mq)
            docker logs -f mq
            ;;
        neo4j)
            docker logs -f neo4j
            ;;
        *)
            log_error "未知的服务: $service"
            return 1
            ;;
    esac
}

# 显示帮助信息
show_help() {
    cat << 'EOF'
Docker 容器管理脚本

用法: ./scripts/docker-services.sh [命令] [参数]

命令:
  up              创建所有容器 (默认)
  status          显示容器状态
  logs <service>  查看容器日志
  stop            停止所有容器
  delete          删除所有容器

账号密码:
  在项目根目录 .env 中配置（复制 .env.example 后修改），支持以下变量:
    MYSQL_ROOT_PASSWORD  MySQL 密码（用户名固定为 root）
    POSTGRES_USER / POSTGRES_PASSWORD
    REDIS_PASSWORD       Redis 密码
    ES_SECURITY_ENABLED / ES_PASSWORD / ES_HEAP_SIZE
                         ElasticSearch 是否开启安全认证、密码（用户 elastic）与堆内存
    ES_VERSION / ES_IK_ENABLED
                         ElasticSearch 版本（与 IK 插件版本一致）及是否自动安装 IK 分词器
    ES_IK_OFFLINE / ES_IK_OFFLINE_ZIP
                         IK 分词器是否强制使用离线包，以及离线 zip 的宿主机绝对路径
  IK 分词器会在 ES 启动前自动安装、启动后自动验证，无需手动操作
  离线包优先规则: ES_IK_OFFLINE=true 时只用离线包；否则配置了 ES_IK_OFFLINE_ZIP
  且文件存在时优先离线，失败再尝试在线地址
    MONGO_USER / MONGO_PASSWORD
    CLICKHOUSE_USER / CLICKHOUSE_PASSWORD
    RABBITMQ_USER / RABBITMQ_PASSWORD
    NEO4J_USER / NEO4J_PASSWORD
  未单独设置时，MySQL 与 PostgreSQL 密码回退到兼容变量 DB_PASSWORD
  容器已存在时修改密码不会生效，需先执行 delete 再 up

服务列表:
  - mysql         MySQL 数据库 (端口 3306)
  - postgresql    PostgreSQL 数据库 (端口 5432)
  - redis         Redis 缓存 (端口 6379)
  - mongodb       MongoDB 数据库 (端口 27017)
  - clickhouse    ClickHouse 分析数据库 (端口 8123)
  - elasticsearch ElasticSearch 搜索引擎 (端口 9200)
  - nacos         Nacos 服务发现 (端口 8848)
  - rabbitmq      RabbitMQ 消息队列 (端口 5672)
  - neo4j         Neo4j 知识图谱数据库 (端口 7474, 7687)

示例:
  ./scripts/docker-services.sh up               # 创建所有容器
  ./scripts/docker-services.sh status           # 显示容器状态
  ./scripts/docker-services.sh logs mysql       # 查看 MySQL 日志
  ./scripts/docker-services.sh logs rabbitmq    # 查看 RabbitMQ 日志
  ./scripts/docker-services.sh logs neo4j       # 查看 Neo4j 日志
  ./scripts/docker-services.sh stop             # 停止所有容器

EOF
}

# 主函数
main() {
    local command=${1:-up}

    case $command in
        help|--help|-h)
            show_help
            ;;
        status)
            check_docker
            check_docker_daemon
            show_status
            ;;
        logs)
            check_docker
            check_docker_daemon
            show_logs "$2"
            ;;
        stop)
            check_docker
            check_docker_daemon
            stop_all
            ;;
        delete)
            check_docker
            check_docker_daemon
            delete_all
            ;;
        up)
            log_info "========================================"
            log_info "Docker 容器创建脚本"
            log_info "========================================"
            echo ""

            # 检查 Docker
            check_docker
            check_docker_daemon
            echo ""

            # 检查账号密码配置
            check_credentials
            echo ""

            # 准备目录和网络
            prepare_directories
            create_docker_network "hcsy"
            echo ""

            # 创建容器
            create_mysql
            create_postgresql
            create_redis
            create_mongodb
            create_clickhouse
            create_elasticsearch
            create_nacos
            create_rabbitmq
            create_neo4j
            echo ""

            # 显示状态
            show_status

            log_info "所有容器创建完成!"
            echo ""
            log_info "数据库访问信息:"
            echo "  MySQL:         localhost:3306 (root/$MYSQL_ROOT_PASSWORD)"
            echo "  PostgreSQL:    localhost:5432 ($POSTGRES_USER/$POSTGRES_PASSWORD)"
            echo "  Redis:         localhost:6379 (密码: $REDIS_PASSWORD)"
            echo "  MongoDB:       localhost:27017 ($MONGO_USER/$MONGO_PASSWORD)"
            echo "  ClickHouse:    localhost:8123 ($CLICKHOUSE_USER/$CLICKHOUSE_PASSWORD)"
            if es_security_on; then
                echo "  ElasticSearch: http://localhost:9200 (elastic/$ES_PASSWORD)"
            else
                echo "  ElasticSearch: http://localhost:9200 (未开启认证)"
            fi
            echo "  Nacos:         http://localhost:8848"
            echo "  RabbitMQ:      http://localhost:15672 ($RABBITMQ_USER/$RABBITMQ_PASSWORD)"
            echo "  Neo4j:         http://localhost:7474 ($NEO4J_USER/$NEO4J_PASSWORD), Bolt: localhost:7687"
            echo ""
            log_info "账号密码可在项目根目录 .env 中修改（参考 .env.example），修改后需先 delete 再 up"
            echo ""
            ;;
        *)
            log_error "未知命令: $command"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# 运行主函数
main "$@"

#!/bin/bash

# Docker 容器管理脚本
# 用于创建和管理项目所需的 Docker 容器

set -e

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
        -e MYSQL_ROOT_PASSWORD=123 \
        -v ~/mysql/data:/var/lib/mysql \
        -v ~/mysql/conf:/etc/mysql/conf.d \
        -v ~/mysql/init:/docker-entrypoint-initdb.d \
        --network hcsy \
        --restart=always \
        mysql:latest
    
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
        -e POSTGRES_USER=postgres \
        -e POSTGRES_PASSWORD=123456 \
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
        redis:7 redis-server --appendonly yes
    
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
        -e MONGO_INITDB_ROOT_USERNAME=root \
        -e MONGO_INITDB_ROOT_PASSWORD=123456 \
        -v ~/mongo_data:/data/db \
        --network hcsy \
        --restart=always \
        mongo:6
    
    log_info "MongoDB 容器创建成功 (端口 27017)"
}

# Elasticsearch 容器
create_elasticsearch() {
    log_info "创建 Elasticsearch 容器..."
    
    if check_port 9200 "Elasticsearch"; then
        log_warn "Elasticsearch 已存在，是否安装 IK 分词器? (y/n)"
        read -p "请输入: " install_ik
        if [[ "$install_ik" =~ ^[Yy]$ ]]; then
            install_elasticsearch_ik_plugin
        fi
        return 0
    fi
    
    docker run -d \
        --name es \
        -e "ES_JAVA_OPTS=-Xms512m -Xmx512m" \
        -e "discovery.type=single-node" \
        -v es-data:/usr/share/elasticsearch/data \
        -v es-plugins:/usr/share/elasticsearch/plugins \
        --privileged \
        --network hcsy \
        --restart=always \
        -p 9200:9200 \
        -p 9300:9300 \
        elasticsearch:7.12.1
    
    log_info "Elasticsearch 容器创建成功 (端口 9200, 9300)"
    
    # 等待 Elasticsearch 启动
    log_info "等待 Elasticsearch 启动 (约 30 秒)..."
    sleep 30
    
    # 询问是否安装 IK 分词器
    log_warn "是否安装 IK 分词器? (y/n)"
    read -p "请输入: " install_ik
    if [[ "$install_ik" =~ ^[Yy]$ ]]; then
        install_elasticsearch_ik_plugin
    fi
}

# 安装 Elasticsearch IK 分词器插件
install_elasticsearch_ik_plugin() {
    log_info "安装 Elasticsearch IK 分词器插件..."
    
    docker exec -it es elasticsearch-plugin install https://release.infinilabs.com/analysis-ik/7.12.1/elasticsearch-analysis-ik-7.12.1.zip
    
    log_info "IK 分词器安装完成，重启 Elasticsearch 容器..."
    docker restart es
    
    log_info "Elasticsearch 容器已重启"
}

# Nacos 容器
create_nacos() {
    log_info "创建 Nacos 容器..."
    
    if check_port 8848 "Nacos"; then
        return 0
    fi
    
    # 检查 nacos/custom.env 是否存在
    if [ ! -f "nacos/custom.env" ]; then
        log_warn "nacos/custom.env 文件不存在，将使用默认配置"
        mkdir -p nacos
        cat > nacos/custom.env << 'EOF'
MODE=standalone
NACOS_AUTH_ENABLE=false
SPRING_DATASOURCE_PLATFORM=mysql
MYSQL_SERVICE_HOST=mysql
MYSQL_SERVICE_PORT=3306
MYSQL_SERVICE_USER=root
MYSQL_SERVICE_PASSWORD=123
MYSQL_SERVICE_DB_NAME=nacos
EOF
    fi
    
    docker run -d \
        --name nacos \
        --env-file ./nacos/custom.env \
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
        -e RABBITMQ_DEFAULT_USER=itheima \
        -e RABBITMQ_DEFAULT_PASS=123321 \
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

# 显示所有容器状态
show_status() {
    echo ""
    log_info "容器状态:"
    echo ""
    docker ps --format 'table {{.Names}}\t{{.Ports}}\t{{.Status}}' | grep -E "mysql|pgvector|redis|mongodb|es|nacos|mq" || echo "没有相关容器运行"
    echo ""
}

# 停止所有容器
stop_all() {
    log_warn "停止所有容器..."
    
    for container in mysql pgvector-db redis mongodb es nacos mq; do
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
    
    for container in mysql pgvector-db redis mongodb es nacos mq; do
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
        echo "可用服务: mysql, postgresql, redis, mongodb, elasticsearch, nacos, rabbitmq"
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
        nacos)
            docker logs -f nacos
            ;;
        rabbitmq|mq)
            docker logs -f mq
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

用法: ./services.sh docker [命令] [参数]

命令:
  up              创建所有容器 (默认)
  status          显示容器状态
  logs <service>  查看容器日志
  stop            停止所有容器
  delete          删除所有容器

服务列表:
  - mysql         MySQL 数据库 (端口 3306)
  - postgresql    PostgreSQL 数据库 (端口 5432)
  - redis         Redis 缓存 (端口 6379)
  - mongodb       MongoDB 数据库 (端口 27017)
  - elasticsearch Elasticsearch 搜索引擎 (端口 9200)
  - nacos         Nacos 服务发现 (端口 8848)
  - rabbitmq      RabbitMQ 消息队列 (端口 5672)

示例:
  ./services.sh docker up               # 创建所有容器
  ./services.sh docker status           # 显示容器状态
  ./services.sh docker logs mysql       # 查看 MySQL 日志
  ./services.sh docker logs rabbitmq    # 查看 RabbitMQ 日志
  ./services.sh docker stop             # 停止所有容器

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
            
            # 准备目录和网络
            prepare_directories
            create_docker_network "hcsy"
            echo ""
            
            # 创建容器
            create_mysql
            create_postgresql
            create_redis
            create_mongodb
            create_elasticsearch
            create_nacos
            create_rabbitmq
            echo ""
            
            # 显示状态
            show_status
            
            log_info "所有容器创建完成!"
            echo ""
            log_info "数据库访问信息:"
            echo "  MySQL:       localhost:3306 (root/123)"
            echo "  PostgreSQL:  localhost:5432 (postgres/123456)"
            echo "  Redis:       localhost:6379"
            echo "  MongoDB:     localhost:27017 (root/123456)"
            echo "  Elasticsearch: http://localhost:9200"
            echo "  Nacos:       http://localhost:8848"
            echo "  RabbitMQ:    http://localhost:15672 (itheima/123321)"
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

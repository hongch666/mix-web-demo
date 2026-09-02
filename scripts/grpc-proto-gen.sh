#!/usr/bin/env bash

set -uo pipefail

WORKDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROTO_ROOT="${WORKDIR}/proto"
FILTER=""
LIST_ONLY=0
FAILED=0
PYTHON_BIN=""
GO_BIN=""

# 每行格式：proto 文件|服务端|客户端列表|生成语言列表。
MATRIX=(
  "fastapi/search_enhance.proto|fastapi|gozero|python,go"
  "fastapi/algorithm.proto|fastapi|gozero|python,go"
  "fastapi/ai_history.proto|fastapi|gozero|python,go"
  "fastapi/task.proto|fastapi|spring|python,java"
  "gozero/task.proto|gozero|spring|go,java"
  "gozero/sql_tools.proto|gozero|fastapi|go,python"
  "spring/article.proto|spring|gozero,fastapi,nestjs|java,go,python,typescript"
  "spring/category.proto|spring|gozero,fastapi|java,go,python"
  "spring/statistics.proto|spring|fastapi,nestjs|java,python,typescript"
  "spring/user.proto|spring|gozero,fastapi,nestjs|java,go,python,typescript"
  "spring/interaction.proto|spring|gozero,fastapi|java,go,python"
  "nestjs/log.proto|nestjs|gozero,fastapi|typescript,go,python"
  "nestjs/email.proto|nestjs|spring|typescript,java"
)

log_info() { printf '[信息] %s\n' "$1"; }
log_warn() { printf '[警告] %s\n' "$1" >&2; }
log_error() { printf '[错误] %s\n' "$1" >&2; }

usage() {
  printf '用法：%s [-l] [-p 文件名]\n' "$0"
  printf '默认会自动安装缺少的 proto 生成工具，-l 只查看矩阵不安装。\n'
}

while getopts ':lp:' option; do
  case "${option}" in
    l) LIST_ONLY=1 ;;
    p) FILTER="${OPTARG}" ;;
    *) usage; exit 2 ;;
  esac
done

find_python() {
  local candidate
  for candidate in \
    "${WORKDIR}/fastapi/.venv/bin/python" \
    "${WORKDIR}/dist/fastapi/.venv/bin/python" \
    "python3"; do
    if command -v "${candidate}" >/dev/null 2>&1 || [[ -x "${candidate}" ]]; then
      if "${candidate}" -c 'import grpc_tools.protoc' >/dev/null 2>&1; then
        printf '%s' "${candidate}"
        return 0
      fi
    fi
  done
  return 1
}

has_command() { command -v "$1" >/dev/null 2>&1; }

find_python_runtime() {
  local candidate
  for candidate in \
    "${GRPC_PROTO_PYTHON:-}" \
    "${WORKDIR}/fastapi/.venv/bin/python" \
    "${WORKDIR}/dist/fastapi/.venv/bin/python" \
    "python3"; do
    if [[ -n "${candidate}" ]] && { [[ -x "${candidate}" ]] || command -v "${candidate}" >/dev/null 2>&1; }; then
      printf '%s' "${candidate}"
      return 0
    fi
  done
  return 1
}

install_python_tools() {
  local python_bin
  python_bin="$(find_python_runtime)" || {
    log_error "未找到 Python，无法安装 grpcio-tools"
    return 1
  }

  if "${python_bin}" -c 'import grpc_tools.protoc' >/dev/null 2>&1; then
    PYTHON_BIN="${python_bin}"
    return 0
  fi

  if has_command uv; then
    log_info "正在向 FastAPI 虚拟环境安装 grpcio-tools"
    UV_CACHE_DIR="${WORKDIR}/.tmp/uv-cache" uv pip install \
      --python "${python_bin}" "grpcio-tools>=1.67.0" || {
      log_error "安装 grpcio-tools 失败，请检查网络或执行：uv pip install --python ${python_bin} grpcio-tools"
      return 1
    }
  elif "${python_bin}" -m pip --version >/dev/null 2>&1; then
    log_info "正在向 FastAPI Python 环境安装 grpcio-tools"
    "${python_bin}" -m pip install "grpcio-tools>=1.67.0" || {
      log_error "安装 grpcio-tools 失败，请执行：${python_bin} -m pip install grpcio-tools"
      return 1
    }
  else
    log_error "未找到 uv 或 pip，无法自动安装 grpcio-tools"
    return 1
  fi

  "${python_bin}" -c 'import grpc_tools.protoc' >/dev/null 2>&1 || {
    log_error "grpcio-tools 安装后仍无法导入，请检查 Python 环境"
    return 1
  }
  PYTHON_BIN="${python_bin}"
}

install_protoc() {
  has_command protoc && return 0

  if has_command apt-get; then
    log_info "正在通过 apt-get 安装 protobuf-compiler"
    local apt_command=(apt-get)
    local apt_options=(-o Acquire::ForceIPv4=true -o Acquire::Retries=2)
    if [[ "$(id -u)" -eq 0 ]]; then
      apt_command=(apt-get)
    elif has_command sudo; then
      apt_command=(sudo apt-get)
    else
      log_error "安装 protoc 需要 root 权限，请执行：sudo apt-get update && sudo apt-get install -y protobuf-compiler"
      return 1
    fi

    if "${apt_command[@]}" "${apt_options[@]}" update &&
      "${apt_command[@]}" "${apt_options[@]}" install -y protobuf-compiler; then
      :
    else
      log_warn "Ubuntu 官方软件源不可访问，准备切换到临时镜像源"
      local mirror="${GRPC_PROTO_APT_MIRROR:-https://mirrors.aliyun.com/ubuntu}"
      local source_file
      source_file="$(mktemp /tmp/mix-web-demo-apt-sources.XXXXXX)"
      printf '%s\n' \
        "deb ${mirror}/ noble noble-updates noble-backports main universe restricted multiverse" \
        "deb ${mirror}/ noble-security main universe restricted multiverse" > "${source_file}"
      if ! "${apt_command[@]}" \
        "${apt_options[@]}" \
        -o "Dir::Etc::sourcelist=${source_file}" \
        -o Dir::Etc::sourceparts=- \
        update || ! "${apt_command[@]}" \
        "${apt_options[@]}" \
        -o "Dir::Etc::sourcelist=${source_file}" \
        -o Dir::Etc::sourceparts=- \
        install -y protobuf-compiler; then
        rm -f "${source_file}"
        log_error "Ubuntu 官方源和临时镜像源均无法访问，请配置代理或手动安装 protoc"
        return 1
      fi
      rm -f "${source_file}"
    fi
  elif has_command brew; then
    log_info "正在通过 Homebrew 安装 protobuf"
    brew install protobuf
  elif has_command apk; then
    log_info "正在通过 apk 安装 protobuf"
    apk add --no-cache protobuf
  else
    log_error "未识别系统包管理器，请手动安装 protoc"
    return 1
  fi

  has_command protoc || {
    log_error "protoc 安装后仍无法执行，请确认 protoc 已加入 PATH"
    return 1
  }
}

install_go_tools() {
  has_command go || {
    log_error "未找到 Go，无法安装 Go protobuf 插件"
    return 1
  }

  GO_BIN="$(go env GOBIN)"
  if [[ -z "${GO_BIN}" ]]; then
    GO_BIN="$(go env GOPATH)/bin"
  fi
  mkdir -p "${GO_BIN}"
  export PATH="${GO_BIN}:${PATH}"

  if ! has_command protoc-gen-go; then
    log_info "正在安装 protoc-gen-go"
    go install google.golang.org/protobuf/cmd/protoc-gen-go@v1.36.11 || {
      log_error "安装 protoc-gen-go 失败，请执行：go install google.golang.org/protobuf/cmd/protoc-gen-go@v1.36.11"
      return 1
    }
  fi
  if ! has_command protoc-gen-go-grpc; then
    log_info "正在安装 protoc-gen-go-grpc"
    go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@v1.5.1 || {
      log_error "安装 protoc-gen-go-grpc 失败，请执行：go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@v1.5.1"
      return 1
    }
  fi

  has_command protoc-gen-go && has_command protoc-gen-go-grpc
}

generate_python() {
  local proto_file="$1"
  install_python_tools || {
    log_error "未找到可用的 grpc_tools.protoc Python 环境"
    return 1
  }
  mkdir -p "${WORKDIR}/fastapi/app/proto"
  "${PYTHON_BIN}" -m grpc_tools.protoc \
    -I "${PROTO_ROOT}" \
    --python_out="${WORKDIR}/fastapi/app/proto" \
    --grpc_python_out="${WORKDIR}/fastapi/app/proto" \
    "${PROTO_ROOT}/common/result.proto" \
    "${PROTO_ROOT}/${proto_file}"
  # protoc 默认生成顶层 common/fastapi 包，改为项目包路径避免与 FastAPI 包名冲突。
  find "${WORKDIR}/fastapi/app/proto" -type f -name '*_pb2*.py' -print0 |
    xargs -0 sed -i \
      -e 's/^from common import /from app.proto.common import /' \
      -e 's/^from fastapi import /from app.proto.fastapi import /'
}

generate_go() {
  local proto_file="$1"
  local compiler=()
  # grpcio-tools 自带 protoc 编译器，优先使用它，避免依赖系统软件源。
  if install_python_tools; then
    compiler=("${PYTHON_BIN}" -m grpc_tools.protoc)
  else
    install_protoc || return 1
    compiler=(protoc)
  fi
  install_go_tools || return 1
  mkdir -p "${WORKDIR}/gozero/app/proto"
  "${compiler[@]}" \
    -I "${PROTO_ROOT}" \
    --go_out="${WORKDIR}/gozero/app" \
    --go_opt=module=app \
    --go-grpc_out="${WORKDIR}/gozero/app" \
    --go-grpc_opt=module=app \
    "${PROTO_ROOT}/common/result.proto" \
    "${PROTO_ROOT}/${proto_file}"
}

generate_java() {
  local proto_file="$1"
  has_command protoc || {
    log_error "未找到 protoc，无法生成 Java proto 代码"
    return 1
  }
  mkdir -p "${WORKDIR}/spring/src/main/java"
  protoc -I "${PROTO_ROOT}" \
    --java_out="${WORKDIR}/spring/src/main/java" \
    "${PROTO_ROOT}/common/result.proto" \
    "${PROTO_ROOT}/${proto_file}"

  if has_command protoc-gen-grpc-java; then
    protoc -I "${PROTO_ROOT}" \
      --plugin="protoc-gen-grpc-java=$(command -v protoc-gen-grpc-java)" \
      --grpc-java_out="${WORKDIR}/spring/src/main/java" \
      "${PROTO_ROOT}/common/result.proto" \
      "${PROTO_ROOT}/${proto_file}"
  else
    log_warn "未找到 protoc-gen-grpc-java，仅生成 Java protobuf 消息类"
  fi
}

generate_typescript() {
  local proto_file="$1"
  local plugin="${WORKDIR}/nestjs/node_modules/.bin/protoc-gen-ts_proto"
  if [[ ! -x "${plugin}" ]]; then
    plugin="${WORKDIR}/node_modules/.bin/protoc-gen-ts_proto"
  fi
  if [[ ! -x "${plugin}" ]]; then
    has_command npm || {
      log_error "未找到 npm，无法安装 ts-proto"
      return 1
    }
    log_info "正在向 NestJS 开发依赖安装 ts-proto"
    (cd "${WORKDIR}/nestjs" && npm install --no-save --no-audit --no-fund \
      --registry="${GRPC_PROTO_NPM_REGISTRY:-https://registry.npmmirror.com}" ts-proto) || {
      log_error "安装 ts-proto 失败，请在 nestjs 目录执行：npm install"
      return 1
    }
  fi
  if [[ ! -x "${plugin}" ]]; then
    log_error "ts-proto 安装后仍不可用，请检查 NestJS 依赖"
    return 1
  fi
  mkdir -p "${WORKDIR}/nestjs/src/proto"
  protoc -I "${PROTO_ROOT}" \
    --plugin="protoc-gen-ts_proto=${plugin}" \
    --ts_proto_out="${WORKDIR}/nestjs/src/proto" \
    --ts_proto_opt=nestJs=true,outputServices=grpc-js,esModuleInterop=true \
    "${PROTO_ROOT}/common/result.proto" \
    "${PROTO_ROOT}/${proto_file}"
}

selected=0
for row in "${MATRIX[@]}"; do
  IFS='|' read -r proto_file server consumers languages <<< "${row}"
  if [[ -n "${FILTER}" && "$(basename "${proto_file}")" != "${FILTER}" ]]; then
    continue
  fi
  selected=1
  if [[ ! -f "${PROTO_ROOT}/${proto_file}" ]]; then
    log_warn "proto 文件不存在，跳过：${proto_file}"
    continue
  fi
  if [[ "${LIST_ONLY}" -eq 1 ]]; then
    log_info "${proto_file}：服务端=${server}，客户端=${consumers}，生成=${languages}"
    continue
  fi
  IFS=',' read -ra language_list <<< "${languages}"
  for language in "${language_list[@]}"; do
    case "${language}" in
      python) log_info "生成 ${proto_file} 的 Python 代码"; generate_python "${proto_file}" || FAILED=1 ;;
      go) log_info "生成 ${proto_file} 的 Go 代码"; generate_go "${proto_file}" || FAILED=1 ;;
      java) log_info "生成 ${proto_file} 的 Java 代码"; generate_java "${proto_file}" || FAILED=1 ;;
      typescript) log_info "生成 ${proto_file} 的 TypeScript 代码"; generate_typescript "${proto_file}" || FAILED=1 ;;
      *) log_error "不支持的 proto 生成语言：${language}"; FAILED=1 ;;
    esac
  done
done

if [[ "${selected}" -eq 0 ]]; then
  log_warn "没有匹配的 proto，不检查生成工具"
  exit 0
fi

exit "${FAILED}"

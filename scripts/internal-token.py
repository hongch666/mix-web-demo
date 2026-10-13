#!/usr/bin/env python3

# 脚本说明：
# 签发一枚内部服务令牌（用 INTERNAL_TOKEN_SECRET 签发的 HS256 JWT），供本地与接口测试直接调用内部接口
# 四个服务的内部接口都只校验 X-Internal-Token 的签名与有效期（见各自的 InternalTokenAspect /
# InternalServiceMiddleware / InternalTokenGuard / requireInternalToken），签名密钥在各自的 .env
# 中且取值一致，因此本脚本签发的令牌对四个服务通用，不需要启动服务，也不需要跑单测打印令牌
# 只依赖 Python 标准库，不引入 PyJWT 等第三方库
#
# 入口说明：日常使用走 ./mix token（scripts/internal-token.sh），它按服务逐个调用本脚本，
# 并把结果写入 Apifox 环境变量；本脚本只负责单枚令牌的签发与输出，可单独调用
#
# 用法：python scripts/internal-token.py --service-name spring [options]
#   --service-name NAME 令牌里的 serviceName，默认 local-dev
#   --user-id N         令牌里的 userId，-1 表示系统调用（默认 -1）
#   --ttl 24h           有效期，支持 30s / 5m / 2h / 7d 或纯秒数（默认 24h）
#   --secret VALUE      直接指定签名密钥，优先于 .env 与环境变量
#   --env-file PATH     指定读取 INTERNAL_TOKEN_SECRET 的 .env 文件
#   --header            输出可直接粘贴到 curl 的 X-Internal-Token 请求头
#   --json              以 JSON 输出令牌与元信息
#   --quiet             不向 stderr 打印密钥来源与有效期等元信息
#
# 注意：四个服务都会剥掉请求头里的 Bearer 前缀，所以发送时必须写成
#   X-Internal-Token: Bearer <token>
# 缺少 Bearer 前缀会被当成没有携带令牌并返回 401

from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent

SECRET_ENV_NAME = "INTERNAL_TOKEN_SECRET"
DEFAULT_USER_ID = -1
DEFAULT_SERVICE_NAME = "local-dev"
DEFAULT_TTL_SECONDS = 24 * 60 * 60
TTL_UNITS = {"s": 1, "m": 60, "h": 3600, "d": 86400}
HEADER_NAME = "X-Internal-Token"

# 密钥查找顺序：根目录 .env 之后按服务目录逐个查找，四份取值一致时命中第一个
ENV_FILE_CANDIDATES = (
    ROOT_DIR / ".env",
    ROOT_DIR / "spring" / ".env",
    ROOT_DIR / "nestjs" / ".env",
    ROOT_DIR / "gozero" / "app" / ".env",
    ROOT_DIR / "fastapi" / ".env",
)


def base64url(data: bytes) -> str:
    """按 JWT 规范做无填充的 base64url 编码"""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def parse_ttl(raw: str) -> int:
    """解析有效期，支持 30s / 5m / 2h / 7d 或纯秒数"""
    text = raw.strip().lower()
    if not text:
        raise ValueError("有效期不能为空，支持 30s / 5m / 2h / 7d 或纯秒数")

    unit = text[-1]
    if unit in TTL_UNITS:
        number_text = text[:-1]
        factor = TTL_UNITS[unit]
    else:
        number_text = text
        factor = 1

    if not number_text.isdigit():
        raise ValueError(f"无法解析有效期 {raw}，支持 30s / 5m / 2h / 7d 或纯秒数")

    seconds = int(number_text) * factor
    if seconds <= 0:
        raise ValueError("有效期必须大于 0 秒")
    return seconds


def read_env_value(path: Path, name: str) -> Optional[str]:
    """从 .env 文件读取指定变量，忽略注释行并去掉值两侧的引号"""
    if not path.is_file():
        return None

    try:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError:
        return None

    for line in lines:
        text = line.strip()
        if not text or text.startswith("#") or "=" not in text:
            continue

        key, _, raw = text.partition("=")
        key = key.strip()
        if key.startswith("export "):
            key = key[len("export ") :].strip()
        if key != name:
            continue

        value = raw.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        if value:
            return value

    return None


def resolve_secret(explicit: Optional[str], env_file: Optional[str]) -> tuple[str, str]:
    """返回 (密钥, 来源说明)，按「参数 → 进程环境变量 → 指定 .env → 默认 .env 清单」顺序查找"""
    if explicit:
        return explicit, "--secret 参数"

    from_environment = os.environ.get(SECRET_ENV_NAME, "").strip()
    if from_environment:
        return from_environment, f"环境变量 {SECRET_ENV_NAME}"

    if env_file:
        path = Path(env_file).expanduser()
        value = read_env_value(path, SECRET_ENV_NAME)
        if value:
            return value, str(path)
        raise LookupError(f"{path} 中没有读到 {SECRET_ENV_NAME}")

    for candidate in ENV_FILE_CANDIDATES:
        value = read_env_value(candidate, SECRET_ENV_NAME)
        if value:
            return value, str(candidate)

    searched = "、".join(str(path) for path in ENV_FILE_CANDIDATES)
    raise LookupError(
        f"没有找到 {SECRET_ENV_NAME}，已查找：{searched}；"
        "请在对应 .env 中配置，或用 --secret / --env-file 显式指定"
    )


def build_token(
    secret: str, user_id: int, service_name: str, ttl_seconds: int
) -> tuple[str, int]:
    """签发内部令牌，返回 (令牌, 过期时间戳)。声明结构与四个服务的签发实现保持一致"""
    issued_at = int(time.time())
    expires_at = issued_at + ttl_seconds

    header: dict[str, Any] = {"alg": "HS256", "typ": "JWT"}
    payload: dict[str, Any] = {
        "userId": user_id,
        "serviceName": service_name,
        "tokenType": "internal",
        "sub": "internal_service_token",
        "iat": issued_at,
        "nbf": issued_at,
        "exp": expires_at,
    }

    segments = ".".join(
        base64url(
            json.dumps(part, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        )
        for part in (header, payload)
    )
    signature = hmac.new(
        secret.encode("utf-8"), segments.encode("ascii"), hashlib.sha256
    ).digest()
    return f"{segments}.{base64url(signature)}", expires_at


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="./mix token",
        description="生成内部服务令牌（INTERNAL_TOKEN_SECRET 签发的 HS256 JWT）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "示例：\n"
            "  ./mix token --user-id 10001 --service-name spring --ttl 2h\n"
            "  ./mix token --header\n"
            "请求头格式：X-Internal-Token: Bearer <token>"
        ),
    )
    parser.add_argument(
        "--user-id",
        type=int,
        default=DEFAULT_USER_ID,
        help="令牌里的 userId，-1 表示系统调用（默认 -1）",
    )
    parser.add_argument(
        "--service-name",
        default=DEFAULT_SERVICE_NAME,
        help=f"令牌里的 serviceName（默认 {DEFAULT_SERVICE_NAME}）",
    )
    parser.add_argument(
        "--ttl",
        default=f"{DEFAULT_TTL_SECONDS // 3600}h",
        help="有效期，支持 30s / 5m / 2h / 7d 或纯秒数（默认 24h）",
    )
    parser.add_argument(
        "--secret", default=None, help="直接指定签名密钥，优先于 .env 与环境变量"
    )
    parser.add_argument(
        "--env-file", default=None, help="指定读取 INTERNAL_TOKEN_SECRET 的 .env 文件"
    )
    parser.add_argument(
        "--header",
        action="store_true",
        help="输出可直接粘贴到 curl 的 X-Internal-Token 请求头",
    )
    parser.add_argument("--json", action="store_true", help="以 JSON 输出令牌与元信息")
    parser.add_argument(
        "--quiet", action="store_true", help="不向 stderr 打印密钥来源与有效期等元信息"
    )
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)

    try:
        ttl_seconds = parse_ttl(args.ttl)
    except ValueError as error:
        print(f"参数错误：{error}", file=sys.stderr)
        return 1

    try:
        secret, secret_source = resolve_secret(args.secret, args.env_file)
    except LookupError as error:
        print(f"生成内部令牌失败：{error}", file=sys.stderr)
        return 1

    token, expires_at = build_token(
        secret, args.user_id, args.service_name, ttl_seconds
    )
    expires_text = datetime.fromtimestamp(expires_at).strftime("%Y-%m-%d %H:%M:%S")

    if not args.quiet and not args.json:
        print(f"密钥来源：{secret_source}", file=sys.stderr)
        print(
            f"userId：{args.user_id}  serviceName：{args.service_name}", file=sys.stderr
        )
        print(f"有效期至：{expires_text}（{ttl_seconds} 秒）", file=sys.stderr)
        print(f"请求头：{HEADER_NAME}: Bearer <token>", file=sys.stderr)

    if args.json:
        print(
            json.dumps(
                {
                    "token": token,
                    "header": f"{HEADER_NAME}: Bearer {token}",
                    "userId": args.user_id,
                    "serviceName": args.service_name,
                    "expiresIn": ttl_seconds,
                    "expiresAt": expires_text,
                    "secretSource": secret_source,
                },
                ensure_ascii=False,
            )
        )
    elif args.header:
        print(f"{HEADER_NAME}: Bearer {token}")
    else:
        print(token)

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

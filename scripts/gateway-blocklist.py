#!/usr/bin/env python3
"""读取网关 block-internal 路由的 URI 黑名单，供各服务 OpenAPI 生成器注入 403 响应

网关配置是 URI 黑名单：精确 URI 与以 * 结尾的前缀，两者都是网关层的拦截，
服务的 OpenAPI 产物无法自行推导，必须在生成阶段读取并补 403。

用法：
  python scripts/gateway-blocklist.py --check            # 输出 JSON 清单到 stdout
  python scripts/gateway-blocklist.py --list             # 人类可读清单
  python scripts/gateway-blocklist.py --matches <path>   # 判断某个 OpenAPI path 是否被拦截
  python scripts/gateway-blocklist.py --source           # 输出配置文件路径
"""

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GATEWAY_CONFIG = ROOT / "gateway/apisix/apisix.yaml"

BLOCK_ROUTE_ID = "block-internal"
STATUS = 403
DESCRIPTION = "内部接口禁止外部访问"

# 从 YAML 里抽 block-internal 路由的 uris 列表，不依赖 PyYAML：
# 该列表是缩进的方括号条目，遇到 priority 字段结束
URI_LINE = re.compile(r"^\s*/\S*,\s*$")


def load_blocklist() -> list[str]:
    """返回网关黑名单 URI 列表（保持配置顺序）"""
    text = GATEWAY_CONFIG.read_text(encoding="utf-8")
    lines = text.splitlines()
    start = None
    for idx, line in enumerate(lines):
        if re.match(r"^\s*-\s*id:\s*" + re.escape(BLOCK_ROUTE_ID) + r"\s*$", line):
            start = idx
            break
    if start is None:
        raise RuntimeError(f"网关配置中未找到路由 {BLOCK_ROUTE_ID}: {GATEWAY_CONFIG}")

    block = lines[start:]
    end = next(
        (idx for idx, line in enumerate(block[1:], start=1)
         if re.match(r"^\s*-\s*id:\s*", line)),
        len(block),
    )
    uris = [
        match.group(0).strip().rstrip(",")
        for line in block[1:end]
        if (match := URI_LINE.match(line))
    ]
    if not uris:
        raise RuntimeError(f"路由 {BLOCK_ROUTE_ID} 未解析出任何 URI: {GATEWAY_CONFIG}")
    return uris


def is_blocked(path: str, blocklist: list[str]) -> bool:
    """判断 OpenAPI path 是否落入网关黑名单

    精确条目必须完全相等；以 * 结尾的条目按去星号后的前缀匹配。
    """
    for uri in blocklist:
        if uri.endswith("*"):
            if path.startswith(uri[:-1]):
                return True
        elif path == uri:
            return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description="读取网关内部接口黑名单")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true", help="以 JSON 输出黑名单")
    group.add_argument("--list", action="store_true", help="以文本输出黑名单")
    group.add_argument("--matches", metavar="PATH", help="判断 path 是否被拦截")
    group.add_argument("--source", action="store_true", help="输出配置文件路径")
    args = parser.parse_args()

    if args.source:
        print(GATEWAY_CONFIG)
        return 0

    blocklist = load_blocklist()
    if args.check:
        import json

        # 只写 ASCII 字段：Git Bash 下重定向输出会按系统编码写盘，中文 description 会破坏 UTF-8
        # 各服务生成器自带同样的中文描述常量
        print(json.dumps({"uris": blocklist, "status": STATUS}))
    elif args.list:
        for uri in blocklist:
            print(uri)
    elif args.matches:
        print("blocked" if is_blocked(args.matches, blocklist) else "allowed")
    return 0


if __name__ == "__main__":
    sys.exit(main())

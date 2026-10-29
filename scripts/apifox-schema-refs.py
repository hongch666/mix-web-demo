#!/usr/bin/env python3
"""检查 Apifox 项目导出快照里接口与数据模型的引用完整性

Apifox 把接口的请求体/响应体存成 JSON Schema，模型以 $ref: #/definitions/<模型ID>
的形式指向项目里的数据模型。全量对齐删除或重建模型后，接口上的引用不会自动回滚，
Apifox 的「校验响应」会报 can't resolve reference，本脚本用于同步后自检。

用法：
  python scripts/apifox-schema-refs.py --check <snapshot.apifox.json> --models <模型ID清单>

  snapshot：apifox export --format apifox --scope all --no-include-api-cases 的产物
  模型ID清单：一行一个模型 ID，由 apifox schema list 取出（脚本内部只比 ID，不关心名称）

输出：
  首行 DANGLING=<断链数量>
  随后每行一个断链位置示例（最多 --examples 条，默认 5 条）

退出码：0 无断链；1 存在断链；2 参数或解析失败
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCHEMA_FIELDS = ("requestBody", "responseDefinition", "parameters", "responses")


def iter_endpoints(nodes: list, trail: str = ""):
    """深度遍历 apiCollection，产出（路径, 接口节点）"""
    for node in nodes:
        if not isinstance(node, dict):
            continue
        name = str(node.get("name") or "")
        current = f"{trail}/{name}" if name else trail
        api = node.get("api")
        if isinstance(api, dict):
            label = f"{str(api.get('method') or '').upper()} {api.get('path') or ''}".strip()
            yield current or label, api, label
        for key in ("items", "children", "apiCollection"):
            children = node.get(key)
            if isinstance(children, list):
                yield from iter_endpoints(children, current)


def collect_refs(node: object, found: list[str]) -> None:
    """收集节点里所有 #/definitions/<id> 形式的引用"""
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "$ref" and isinstance(value, str):
                found.append(value)
            else:
                collect_refs(value, found)
    elif isinstance(node, list):
        for item in node:
            collect_refs(item, found)


def definition_ids(node: object) -> set[str]:
    """收集节点内联声明的 definitions ID"""
    found: set[str] = set()
    if isinstance(node, dict):
        for key, value in node.items():
            if key in {"definitions", "$defs"} and isinstance(value, dict):
                found.update(str(item) for item in value)
            else:
                found |= definition_ids(value)
    elif isinstance(node, list):
        for item in node:
            found |= definition_ids(item)
    return found


def load_model_ids(path: Path) -> set[str]:
    """读取模型 ID 清单，兼容纯文本与 apifox schema list 的 JSON 输出"""
    raw = path.read_text(encoding="utf-8-sig").strip()
    if not raw:
        return set()
    if raw.startswith(("{", "[")):
        document = json.loads(raw)
        items = document.get("data") if isinstance(document, dict) else document
        ids: set[str] = set()
        for item in items or []:
            if isinstance(item, dict) and item.get("id") is not None:
                ids.add(str(item["id"]))
        return ids
    return {line.strip() for line in raw.splitlines() if line.strip()}


def main() -> int:
    parser = argparse.ArgumentParser(description="检查 Apifox 项目快照的模型引用完整性")
    parser.add_argument("--check", required=True, help="apifox 格式的导出快照路径")
    parser.add_argument("--models", required=True, help="模型 ID 清单文件")
    parser.add_argument("--examples", type=int, default=5, help="断链示例条数，默认 5")
    args = parser.parse_args()

    try:
        document = json.loads(Path(args.check).read_text(encoding="utf-8"))
        model_ids = load_model_ids(Path(args.models))
    except (OSError, json.JSONDecodeError) as error:
        print(f"[ERROR] 读取失败: {error}")
        return 2

    dangling: list[str] = []
    total = 0
    for trail, api, label in iter_endpoints(document.get("apiCollection") or []):
        total += 1
        for field in SCHEMA_FIELDS:
            block = api.get(field)
            if not block:
                continue
            local = definition_ids(block)
            refs: list[str] = []
            collect_refs(block, refs)
            for ref in refs:
                if not ref.startswith("#/definitions/"):
                    continue
                model_id = ref.rsplit("/", 1)[-1]
                if model_id in local or model_id in model_ids:
                    continue
                dangling.append(f"{trail} | {label} | {field} -> {ref}")

    print(f"DANGLING={len(dangling)}")
    print(f"ENDPOINTS={total}")
    print(f"MODELS={len(model_ids)}")
    for line in dangling[: max(args.examples, 0)]:
        print(line)
    return 0 if not dangling else 1


if __name__ == "__main__":
    sys.exit(main())

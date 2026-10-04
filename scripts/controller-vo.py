#!/usr/bin/env python3
"""控制器返回类型检查（Spring）

约定：控制器的返回类型必须使用具体的 VO 承载，禁止直接返回匿名 Map（Map<String, Object>）
原因：匿名 Map 在 Swagger 中没有字段说明，下游只能靠猜字段名，也无法校验类型

动态结构（列由运行时决定）等确实只能使用 Map 的场景，需要显式豁免：

  // vo-exempt: <原因>          方法级豁免，写在方法或其注解上方
  // vo-exempt-class: <原因>    类级豁免，写在控制器类声明上方

用法：
  python scripts/controller-vo.py --check <路径...>

路径可以是文件或目录，目录下按扩展名收集 .java 文件
退出码：0 通过，1 存在不符合项
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# 控制器方法声明：public 之后到方法名之前是返回类型
METHOD_DECL = re.compile(r"^\s*public\s+(.+?)\s+\w+\s*\(")
# 匿名 Map：兼容 java.util.Map 写法与 Map<String,Object> 无空格写法
ANONYMOUS_MAP = re.compile(r"Map\s*<\s*String\s*,\s*Object\s*>")
CLASS_DECL = re.compile(r"^\s*(public\s+)?(final\s+)?class\s+\w+")
METHOD_EXEMPT = re.compile(r"vo-exempt\s*:")
CLASS_EXEMPT = re.compile(r"vo-exempt-class\s*:")
# 类级豁免扫描范围：类声明上方若干行（含类注释与注解）
CLASS_EXEMPT_LOOKBACK = 10


def collect_files(paths: list[str]) -> list[Path]:
    files: list[Path] = []
    for raw in paths:
        path = Path(raw)
        if path.is_dir():
            files.extend(sorted(path.rglob("*.java")))
        elif path.is_file():
            files.append(path)
        else:
            raise FileNotFoundError(raw)
    return files


def class_exempt_classes(lines: list[str]) -> set[int]:
    """返回带类级豁免的控制器类声明行下标（0-based）"""
    exempt: set[int] = set()
    for index, line in enumerate(lines):
        if not CLASS_DECL.match(line):
            continue
        lower = max(0, index - CLASS_EXEMPT_LOOKBACK)
        for cursor in range(lower, index):
            if CLASS_EXEMPT.search(lines[cursor]):
                exempt.add(index)
                break
    return exempt


def method_exempted(lines: list[str], decl_index: int) -> bool:
    """方法或其注解上方声明的豁免视为有效"""
    cursor = decl_index - 1
    while cursor >= 0:
        stripped = lines[cursor].strip()
        if not stripped:
            break
        if METHOD_EXEMPT.search(lines[cursor]):
            return True
        if stripped.startswith("@"):
            cursor -= 1
            continue
        break
    return False


def enclosing_exempt_class(lines: list[str], decl_index: int, exempt: set[int]) -> bool:
    """方法是否位于带类级豁免的控制器内（取方法上方最近的类声明）"""
    if not exempt:
        return False
    enclosing = None
    for index, line in enumerate(lines):
        if index >= decl_index:
            break
        if CLASS_DECL.match(line):
            enclosing = index
    return enclosing in exempt


def process_file(path: Path) -> list[str]:
    source = path.read_text(encoding="utf-8")
    lines = source.split("\n")
    exempt_classes = class_exempt_classes(lines)

    problems: list[str] = []
    for index, line in enumerate(lines):
        matched = METHOD_DECL.match(line)
        if not matched:
            continue
        if not ANONYMOUS_MAP.search(matched.group(1)):
            continue
        if method_exempted(lines, index):
            continue
        if enclosing_exempt_class(lines, index, exempt_classes):
            continue
        problems.append(
            f"{path}:{index + 1} 控制器返回类型包含匿名 Map，"
            "请改用带 @Schema 的 VO；确需动态结构时在方法上方添加 // vo-exempt: 原因"
        )
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description="控制器返回类型检查（禁止匿名 Map）")
    parser.add_argument("--check", action="store_true", help="只检查不修改文件")
    parser.add_argument("paths", nargs="+", help="待检查的文件与目录")
    args = parser.parse_args()

    try:
        files = collect_files(args.paths)
    except FileNotFoundError as error:
        print(f"[ERROR] 路径不存在: {error}")
        return 1

    failed = False
    for path in files:
        try:
            problems = process_file(path)
        except (UnicodeDecodeError, SyntaxError) as error:
            print(f"[ERROR] {path} 解析失败: {error}")
            failed = True
            continue
        for problem in problems:
            print(f"[ERROR] {problem}")
            failed = True

    if failed:
        print("[ERROR] 控制器返回类型存在匿名 Map，请改用带 @Schema 的 VO 或显式豁免")
        return 1

    print("[INFO] 控制器返回类型检查通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())

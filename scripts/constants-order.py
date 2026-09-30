#!/usr/bin/env python3
"""常量类成员顺序检查与整理

约定：nestjs 与 fastapi 的常量类里，函数型成员必须全部排在普通常量之前
  - NestJS：函数型成员写作 static readonly NAME = (...) => ... 的静态属性
  - FastAPI：函数型成员写作 @staticmethod 修饰的方法

连续的同类成员视为一组，组内原有排版（相邻常量不分隔、注释归属）保持不变，
整理时只在不同的组之间保留一个空行

用法：
  python scripts/constants-order.py --check <路径...>
  python scripts/constants-order.py --fix <路径...>

路径可以是文件或目录，目录下按扩展名收集 .ts 与 .py 文件
退出码：0 通过，1 存在不符合项或整理失败
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from dataclasses import dataclass
from pathlib import Path

FUNCTION = "function"
CONSTANT = "constant"

TS_CLASS_START = re.compile(r"^export class (\w+) \{")
TS_CLASS_END = re.compile(r"^\}[ \t]*$")
TS_MEMBER = re.compile(r"^ {2}static readonly \w+\s*[:=]")
# 缩进限定在 2-3 空格，覆盖 Prettier 排版的 // 注释与 /** */ 块注释（续行为 3 空格）
# 同时避开模板字符串正文里同样以 * 开头但缩进更深的 CSS 片段
TS_COMMENT = re.compile(r"^ {2,3}(//|/\*|\*)")
TS_ASYNC_PREFIX = re.compile(r"^async\s+")

PY_COMMENT = re.compile(r"^ {4}#")


@dataclass(frozen=True)
class ClassRegion:
    """常量类里待校验的成员区域

    start / end 为 0-based 行下标，end 不含
    group_kinds、group_blocks、group_lines 按连续同类成员分组
    """

    name: str
    group_kinds: tuple[str, ...]
    group_blocks: tuple[tuple[str, ...], ...]
    group_lines: tuple[int, ...]
    start: int
    end: int


def strip_trailing_blank(lines: list[str]) -> list[str]:
    """去掉尾部空行，组之间统一由一个空行分隔"""
    end = len(lines)
    while end > 0 and not lines[end - 1].strip():
        end -= 1
    return lines[:end]


def build_region(
    name: str,
    kinds: list[str],
    starts: list[int],
    decls: list[int],
    region_end: int,
    lines: list[str],
) -> ClassRegion:
    """把逐个成员合并成连续同类成员的组"""
    group_kinds: list[str] = []
    group_blocks: list[tuple[str, ...]] = []
    group_lines: list[int] = []

    index = 0
    total = len(kinds)
    while index < total:
        stop_index = index + 1
        while stop_index < total and kinds[stop_index] == kinds[index]:
            stop_index += 1

        stop = starts[stop_index] if stop_index < total else region_end
        group_kinds.append(kinds[index])
        group_blocks.append(tuple(strip_trailing_blank(lines[starts[index] : stop])))
        group_lines.append(decls[index] + 1)
        index = stop_index

    return ClassRegion(
        name=name,
        group_kinds=tuple(group_kinds),
        group_blocks=tuple(group_blocks),
        group_lines=tuple(group_lines),
        start=starts[0],
        end=region_end,
    )


# ==================== NestJS ====================


def typescript_member_kind(lines: list[str], decl: int, limit: int) -> str:
    """按赋值号右侧的首个记号判断成员是函数还是常量"""
    text = lines[decl]
    index = decl + 1
    while "=" not in text and index < limit:
        line = lines[index]
        if not line.strip() or TS_COMMENT.match(line):
            break
        text = f"{text}\n{line}"
        index += 1

    position = text.find("=")
    if position == -1:
        return CONSTANT

    value = TS_ASYNC_PREFIX.sub("", text[position + 1 :].lstrip())
    if value.startswith(("(", "function")):
        return FUNCTION
    return CONSTANT


def typescript_regions(lines: list[str]) -> list[ClassRegion]:
    regions: list[ClassRegion] = []
    index = 0
    while index < len(lines):
        matched = TS_CLASS_START.match(lines[index])
        if not matched:
            index += 1
            continue

        class_start = index
        class_end = class_start + 1
        while class_end < len(lines) and not TS_CLASS_END.match(lines[class_end]):
            class_end += 1

        region = typescript_region(lines, matched.group(1), class_start, class_end)
        if region is not None:
            regions.append(region)
        index = class_end + 1
    return regions


def typescript_region(
    lines: list[str], name: str, class_start: int, class_end: int
) -> ClassRegion | None:
    decls = [i for i in range(class_start + 1, class_end) if TS_MEMBER.match(lines[i])]
    if len(decls) < 2:
        return None

    region_end = class_end
    while region_end - 1 > class_start and not lines[region_end - 1].strip():
        region_end -= 1

    kinds: list[str] = []
    starts: list[int] = []
    for order, decl in enumerate(decls):
        limit = decls[order + 1] if order + 1 < len(decls) else class_end
        kinds.append(typescript_member_kind(lines, decl, limit))

        # 成员上方直属的注释随成员一起移动，不允许越过上一个成员
        lower = class_start + 1 if order == 0 else decls[order - 1] + 1
        start = decl
        while start - 1 >= lower and TS_COMMENT.match(lines[start - 1]):
            start -= 1
        starts.append(start)

    return build_region(name, kinds, starts, decls, region_end, lines)


# ==================== FastAPI ====================


def python_regions(source: str, lines: list[str]) -> list[ClassRegion]:
    tree = ast.parse(source)
    regions: list[ClassRegion] = []
    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        region = python_region(lines, node)
        if region is not None:
            regions.append(region)
    return regions


def python_region(lines: list[str], node: ast.ClassDef) -> ClassRegion | None:
    entries: list[tuple[str, int, int, int]] = []
    for position, item in enumerate(node.body):
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
            kind = FUNCTION
        elif isinstance(item, (ast.Assign, ast.AnnAssign)):
            kind = CONSTANT
        else:
            continue

        decl = item.lineno
        for decorator in getattr(item, "decorator_list", ()):
            decl = min(decl, decorator.lineno)
        entries.append((kind, decl - 1, item.end_lineno, position))

    if len(entries) < 2:
        return None

    kinds: list[str] = []
    starts: list[int] = []
    decls: list[int] = []
    for kind, decl, _, position in entries:
        # 成员上方直属的注释随成员一起移动，不允许越过上一个语句
        lower = node.body[position - 1].end_lineno if position > 0 else node.lineno
        start = decl
        while start - 1 >= lower and PY_COMMENT.match(lines[start - 1]):
            start -= 1
        kinds.append(kind)
        starts.append(start)
        decls.append(decl)

    return build_region(node.name, kinds, starts, decls, entries[-1][2], lines)


# ==================== 公共逻辑 ====================


def first_misplaced_function(group_kinds: tuple[str, ...]) -> int | None:
    """返回第一个排在普通常量之后的函数成员组下标，顺序符合时返回 None"""
    seen_constant = False
    for index, kind in enumerate(group_kinds):
        if kind == CONSTANT:
            seen_constant = True
        elif seen_constant:
            return index
    return None


def ordered_group_lines(region: ClassRegion) -> list[str]:
    """按函数成员在前、普通常量在后的顺序重建区域内容"""
    ordered: list[str] = []
    for kind in (FUNCTION, CONSTANT):
        for group_kind, block in zip(region.group_kinds, region.group_blocks):
            if group_kind != kind:
                continue
            if ordered:
                ordered.append("")
            ordered.extend(block)
    return ordered


def collect_files(paths: list[str]) -> list[Path]:
    files: list[Path] = []
    for raw in paths:
        path = Path(raw)
        if path.is_dir():
            files.extend(
                sorted(item for item in path.iterdir() if item.suffix in {".ts", ".py"})
            )
        elif path.is_file():
            files.append(path)
        else:
            raise FileNotFoundError(raw)
    return files


def process_file(path: Path, fix: bool) -> tuple[list[str], bool]:
    """返回（问题描述列表，文件是否已被写入）"""
    source = path.read_text(encoding="utf-8")
    lines = source.split("\n")

    if path.suffix == ".ts":
        regions = typescript_regions(lines)
    else:
        regions = python_regions(source, lines)

    problems: list[str] = []
    misplaced: list[ClassRegion] = []
    for region in regions:
        index = first_misplaced_function(region.group_kinds)
        if index is None:
            continue
        problems.append(
            f"{path}:{region.group_lines[index]} 常量类 {region.name} 的函数成员排在普通常量之后"
        )
        misplaced.append(region)

    if not (fix and misplaced):
        return problems, False

    # 从后往前替换，避免前面的改动影响后续区域的行下标
    for region in reversed(misplaced):
        lines[region.start : region.end] = ordered_group_lines(region)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(lines))
    return problems, True


def main() -> int:
    parser = argparse.ArgumentParser(description="常量类成员顺序检查与整理")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true", help="只检查不修改文件")
    group.add_argument("--fix", action="store_true", help="自动整理不符合的文件")
    parser.add_argument("paths", nargs="+", help="待检查或整理的文件与目录")
    args = parser.parse_args()

    try:
        files = collect_files(args.paths)
    except FileNotFoundError as error:
        print(f"[ERROR] 路径不存在: {error}")
        return 1

    failed = False
    for path in files:
        try:
            problems, written = process_file(path, args.fix)
        except (SyntaxError, UnicodeDecodeError) as error:
            print(f"[ERROR] {path} 解析失败: {error}")
            failed = True
            continue

        if written:
            print(f"[FIXED] {path} 已按函数成员在前重排成员")
        for problem in problems:
            if args.check:
                print(f"[ERROR] {problem}")
                failed = True
            else:
                print(f"[INFO] {problem}")

    if failed:
        print(
            "[ERROR] 存在不符合常量类成员顺序约定的文件，可执行 ./mix format 自动整理"
        )
        return 1

    print(
        "[INFO] 常量类成员顺序检查通过"
        if args.check
        else "[INFO] 常量类成员顺序整理完成"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

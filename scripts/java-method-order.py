#!/usr/bin/env python3
"""Spring Java 方法可见性顺序检查与整理

规范：类的方法按可见性分组排列，public / protected 方法在前，private 方法在后；
private 方法不得穿插在 public / protected 方法之间。

约束范围：
- 只约束 class 中的实例方法（非 static），字段、构造器、静态初始化块、嵌套类型不参与
- static 方法不参与排序：常量类与工具类的 static 方法通常与 static 字段成对书写，有自己的组织方式
- 只识别带 public / protected / private 修饰符的方法，无修饰符的包私有方法不参与
- 嵌套 class 与顶层 class 同样约束

用法：
  python scripts/java-method-order.py --check <路径...>
  python scripts/java-method-order.py --fix <路径...>

路径可以是文件或目录，目录下递归收集 .java 文件
退出码：0 通过，1 存在不符合项或整理失败
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

SKIP_DIRS = {"target", "build", ".venv", "node_modules", "dist", "__pycache__"}

# 类声明：class 关键字 + 类名（顶层与嵌套）
CLASS_DECL = re.compile(r"\bclass\s+(\w+)")

# 方法声明：可见性修饰符开头，且不是 static，可见性到第一个 '(' 之间不含 '='（排除字段初始化），最后是 方法名(
METHOD_DECL = re.compile(
    r"^\s*(?P<vis>public|protected|private)\s+(?!static\b)(?![^(\n]*=)"
    r"(?P<decl>.*?)\b(?P<name>\w+)\s*\("
)


@dataclass(frozen=True)
class MethodBlock:
    """类内一个方法块的源码行区间，start 含 Javadoc 与注解，end 为方法体结束后的下一行"""

    start: int
    end: int
    name: str
    is_private: bool


def code_mask(source: str) -> list[bool]:
    """标记每个字符是否为代码（注释、字符串、字符字面量中的位置为 False）"""
    n = len(source)
    mask = [True] * n
    i = 0
    while i < n:
        char = source[i]
        nxt = source[i + 1] if i + 1 < n else ""
        if char == "/" and nxt == "/":
            mask[i] = mask[i + 1] = False
            i += 2
            while i < n and source[i] != "\n":
                mask[i] = False
                i += 1
        elif char == "/" and nxt == "*":
            mask[i] = mask[i + 1] = False
            i += 2
            while i < n and not (source[i] == "*" and i + 1 < n and source[i + 1] == "/"):
                mask[i] = False
                i += 1
            if i < n:
                mask[i] = mask[i + 1] = False
                i += 2
        elif char == '"':
            mask[i] = False
            i += 1
            while i < n:
                mask[i] = False
                if source[i] == "\\" and i + 1 < n:
                    mask[i + 1] = False
                    i += 2
                    continue
                if source[i] == '"':
                    i += 1
                    break
                i += 1
        elif char == "'":
            mask[i] = False
            i += 1
            while i < n:
                mask[i] = False
                if source[i] == "\\" and i + 1 < n:
                    mask[i + 1] = False
                    i += 2
                    continue
                if source[i] == "'":
                    i += 1
                    break
                i += 1
        else:
            i += 1
    return mask


def line_starts(source: str) -> list[int]:
    """返回每行起始字符索引，末尾补一个 sentinel 表示文件结尾"""
    starts = [0]
    for index, char in enumerate(source):
        if char == "\n":
            starts.append(index + 1)
    return starts


def line_of(starts: list[int], idx: int) -> int:
    """字符索引转 0-based 行号"""
    for line, start in enumerate(starts):
        if start > idx:
            return line - 1
    return len(starts) - 1


def match_brace(source: str, mask: list[bool], open_idx: int) -> int:
    """从 open_idx（'{'）找匹配的 '}'，返回字符索引，未闭合返回 -1"""
    depth = 0
    i = open_idx
    n = len(source)
    while i < n:
        if not mask[i]:
            i += 1
            continue
        if source[i] == "{":
            depth += 1
        elif source[i] == "}":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return -1


def match_paren(source: str, mask: list[bool], open_idx: int) -> int:
    """从 open_idx（'('）找匹配的 ')'，返回字符索引，未闭合返回 -1"""
    depth = 0
    i = open_idx
    n = len(source)
    while i < n:
        if not mask[i]:
            i += 1
            continue
        if source[i] == "(":
            depth += 1
        elif source[i] == ")":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return -1


def collect_prefix(lines: list[str], decl_line: int) -> int:
    """向上收集方法声明紧邻的 Javadoc 与注解，返回块起始行"""
    start = decl_line
    while start > 0 and lines[start - 1].lstrip().startswith("@"):
        start -= 1
    while start > 0:
        prev = lines[start - 1]
        stripped = prev.strip()
        if stripped.startswith("/**") or stripped.startswith("//"):
            start -= 1
            if stripped.startswith("/**") and stripped.endswith("*/") and len(stripped) > 4:
                break
            continue
        if stripped.startswith("*") or stripped == "*/":
            start -= 1
            continue
        break
    return start


def method_end(source: str, mask: list[bool], starts: list[int], decl_line: int) -> int | None:
    """从方法声明行找方法体结束后的下一行（0-based exclusive），识别失败返回 None"""
    decl_start = starts[decl_line]
    i = decl_start
    while i < len(source) and source[i] != "(":
        i += 1
    if i >= len(source):
        return None
    paren_close = match_paren(source, mask, i)
    if paren_close < 0:
        return None
    j = paren_close + 1
    while j < len(source):
        if not mask[j]:
            j += 1
            continue
        if source[j] in "{;":
            break
        j += 1
    if j >= len(source):
        return None
    if source[j] == ";":
        return line_of(starts, j) + 1
    close = match_brace(source, mask, j)
    if close < 0:
        return None
    return line_of(starts, close) + 1


def brace_delta(source: str, mask: list[bool], line_idx: int, starts: list[int]) -> int:
    """计算一行的代码位置大括号净增减"""
    if line_idx + 1 < len(starts):
        end = starts[line_idx + 1]
    else:
        end = len(source)
    delta = 0
    for i in range(starts[line_idx], end):
        if not mask[i]:
            continue
        if source[i] == "{":
            delta += 1
        elif source[i] == "}":
            delta -= 1
    return delta


def find_classes(
    lines: list[str], source: str, mask: list[bool], starts: list[int]
) -> list[tuple[int, str]]:
    """找所有代码位置的 class 声明，返回 (行号, 类名)"""
    result: list[tuple[int, str]] = []
    for idx, line in enumerate(lines):
        matched = CLASS_DECL.search(line)
        if not matched:
            continue
        col = matched.start(1)
        if col >= len(starts):
            continue
        char_idx = starts[idx] + col
        if char_idx < len(mask) and not mask[char_idx]:
            continue
        result.append((idx, matched.group(1)))
    return result


def analyze_class(
    lines: list[str],
    source: str,
    mask: list[bool],
    starts: list[int],
    decl_line: int,
    class_name: str,
) -> tuple[list[MethodBlock], int, int]:
    """分析一个 class：找 body 范围与直接实例方法，返回 (方法列表, body_open 行, body_close 行)"""
    decl_start = starts[decl_line]
    i = decl_start
    while i < len(source):
        if mask[i] and source[i] == "{":
            break
        i += 1
    if i >= len(source):
        return [], decl_line, decl_line
    body_open = line_of(starts, i)
    body_close_idx = match_brace(source, mask, i)
    if body_close_idx < 0:
        return [], body_open, body_open
    body_close = line_of(starts, body_close_idx)

    methods: list[MethodBlock] = []
    depth = 0
    line_idx = body_open + 1
    while line_idx < body_close:
        line = lines[line_idx]
        if depth == 0:
            matched = METHOD_DECL.match(line)
            if matched and matched.group("name") != class_name:
                vis = matched.group("vis")
                start = collect_prefix(lines, line_idx)
                end = method_end(source, mask, starts, line_idx)
                if end is not None and end <= body_close:
                    methods.append(MethodBlock(start, end, matched.group("name"), vis == "private"))
                    line_idx = end
                    continue
        depth += brace_delta(source, mask, line_idx, starts)
        line_idx += 1
    return methods, body_open, body_close


def collect_files(paths: list[str]) -> list[Path]:
    """展开命令行路径，目录递归收集 .java 文件"""
    files: list[Path] = []
    for raw in paths:
        path = Path(raw)
        if path.is_dir():
            for item in sorted(path.rglob("*.java")):
                if any(part in SKIP_DIRS for part in item.parts):
                    continue
                files.append(item)
        elif path.is_file():
            files.append(path)
        else:
            raise FileNotFoundError(raw)
    return files


def collapse_blank_runs(lines: list[str], limit: int = 2) -> list[str]:
    """把连续空行压缩到指定条数"""
    result: list[str] = []
    blanks = 0
    for line in lines:
        if line.strip():
            blanks = 0
            result.append(line)
            continue
        blanks += 1
        if blanks <= limit:
            result.append(line)
    return result


def misplaced_methods(source: str) -> list[tuple[str, str]]:
    """找出所有违反可见性顺序的方法，返回 [(类名, 方法名), ...]"""
    lines = source.split("\n")
    mask = code_mask(source)
    starts = line_starts(source)

    misplaced: list[tuple[str, str]] = []
    for decl_line, class_name in find_classes(lines, source, mask, starts):
        methods, _, _ = analyze_class(lines, source, mask, starts, decl_line, class_name)
        non_private = [m for m in methods if not m.is_private]
        private = [m for m in methods if m.is_private]
        if not non_private or not private:
            continue
        last_np_end = non_private[-1].end
        for m in private:
            if m.start < last_np_end:
                misplaced.append((class_name, m.name))
    return misplaced


def reorder_source(source: str) -> str:
    """把每个类中穿插在 public/protected 方法之间的 private 方法移动到其后，返回整理后的源码"""
    lines = source.split("\n")
    mask = code_mask(source)
    starts = line_starts(source)
    classes = find_classes(lines, source, mask, starts)

    # 从后往前处理，避免重排一个类后影响其前面类的行号
    for decl_line, class_name in reversed(classes):
        methods, body_open, body_close = analyze_class(
            lines, source, mask, starts, decl_line, class_name
        )
        non_private = [m for m in methods if not m.is_private]
        private = [m for m in methods if m.is_private]
        if not non_private or not private:
            continue
        last_np_end = non_private[-1].end
        if all(m.start >= last_np_end for m in private):
            continue

        body_start = body_open + 1
        private_ranges = [(m.start, m.end) for m in private]

        head = [
            line
            for i, line in enumerate(lines[body_start:last_np_end])
            if not any(s <= body_start + i < e for s, e in private_ranges)
        ]
        tail_private: list[str] = []
        for idx, m in enumerate(private):
            if idx:
                tail_private.append("")
            tail_private.extend(lines[m.start : m.end])
        tail = [
            line
            for i, line in enumerate(lines[last_np_end:body_close])
            if not any(s <= last_np_end + i < e for s, e in private_ranges)
        ]

        lines = lines[:body_start] + head + tail_private + tail + lines[body_close:]
        lines = collapse_blank_runs(lines)
        source = "\n".join(lines)
        mask = code_mask(source)
        starts = line_starts(source)

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Spring Java 方法可见性顺序检查与整理")
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

    if args.fix:
        for path in files:
            try:
                source = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            fixed = reorder_source(source)
            if fixed == source:
                continue
            with path.open("w", encoding="utf-8", newline="\n") as handle:
                handle.write(fixed)
            print(f"[FIXED] {path} 已把 private 方法移到 public/protected 方法之后")

    failed = False
    for path in files:
        try:
            source = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for class_name, method_name in misplaced_methods(source):
            print(
                f"[ERROR] {path} 类 {class_name} 的 private 方法 {method_name} "
                "位于 public/protected 方法之前，应移到类的所有非 private 方法之后"
            )
            failed = True

    if failed:
        print(
            "[ERROR] 存在方法可见性顺序不符合规范的文件：public/protected 方法在前、"
            "private 方法在后，位置问题可用 ./mix format 自动整理"
        )
        return 1

    print(
        "[INFO] 方法可见性顺序检查通过" if args.check else "[INFO] 方法可见性顺序整理完成"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

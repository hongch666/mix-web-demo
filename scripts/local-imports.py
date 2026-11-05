#!/usr/bin/env python3
"""模块级导入规范检查与整理

规范：import / from ... import 一律写在文件顶部，禁止出现在函数体、类体或条件分支里

两类例外，必须在导入语句行尾或上一行写 `# lazy-import: 原因`：
  - 循环依赖：只有延迟导入才能打破导入环（如 app.core.db 的建表/装图函数导入 app.internal.models）
  - 明确的延迟加载：把重量级模块的导入推迟到真正调用时（如 app/__init__.py 的 create_app 门面）

if TYPE_CHECKING: 块内的导入不参与运行时导入，不受本规范约束。

整理范围：直接写在函数体或类体里、且渲染后不超行宽的导入会被搬到顶部对应的导入分组
（标准库 / 第三方 / app 与相对导入，组内按模块名字典序）；以下情况只报位置，需人工处理：
  - 多行括号导入、一条语句导入多个名字
  - 位于 try / if / for 等分支内的导入，上移会改变执行条件

用法：
  python scripts/local-imports.py --check <路径...>
  python scripts/local-imports.py --fix <路径...>

路径可以是文件或目录，目录下递归收集 .py 文件
退出码：0 通过，1 存在不符合项或整理失败
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

SKIP_DIRS = {".venv", "__pycache__", ".ruff_cache", ".pytest_cache"}
# 与 pyproject.toml 的 ruff line-length 保持一致
LINE_LENGTH = 88
MARKER = re.compile(r"#\s*lazy-import:\s*\S")
STDLIB = frozenset(sys.stdlib_module_names)
FIRST_PARTY_ROOTS = frozenset({"app", "main"})

# 导入分组：标准库 -> 第三方 -> 本项目，组间空一行
GROUP_STDLIB = 0
GROUP_THIRD_PARTY = 1
GROUP_FIRST_PARTY = 2

SEP_NONE = ""
SEP_BEFORE = "before"
SEP_AFTER = "after"


@dataclass(frozen=True)
class Finding:
    """一处不符合规范的导入"""

    path: Path
    line: int
    message: str

    def describe(self) -> str:
        return f"{self.path}:{self.line} {self.message}"


def iter_python_files(root: Path) -> Iterator[Path]:
    """递归收集目录下的 Python 文件，跳过本地依赖与缓存目录"""
    for item in sorted(root.rglob("*.py")):
        if any(part in SKIP_DIRS for part in item.parts):
            continue
        yield item


def collect_files(paths: list[str]) -> list[Path]:
    """展开命令行路径，目录递归收集，文件原样返回"""
    files: list[Path] = []
    for raw in paths:
        path = Path(raw)
        if path.is_dir():
            files.extend(iter_python_files(path))
        elif path.is_file():
            files.append(path)
        else:
            raise FileNotFoundError(raw)
    return files


def parse_source(source: str) -> ast.Module | None:
    """解析源码，语法错误时返回 None 交给调用方跳过"""
    try:
        return ast.parse(source)
    except (SyntaxError, ValueError):
        return None


def is_type_checking_test(node: ast.expr) -> bool:
    """判断条件是否为 TYPE_CHECKING（含 typing.TYPE_CHECKING）"""
    if isinstance(node, ast.Name):
        return node.id == "TYPE_CHECKING"
    return isinstance(node, ast.Attribute) and node.attr == "TYPE_CHECKING"


def nested_imports(tree: ast.Module) -> list[tuple[ast.stmt, ast.stmt | None]]:
    """收集非顶层导入

    返回（导入语句，直接所属的 def / class），语句位于分支结构内时第二部分为 None，
    因为它不在任何 def / class 的语句块直系位置
    """
    hits: list[tuple[ast.stmt, ast.stmt | None]] = []

    def walk(node: ast.AST, owner: ast.stmt | None) -> None:
        for child in ast.iter_child_nodes(node):
            # TYPE_CHECKING 块不参与运行时导入，整块跳过
            if isinstance(child, ast.If) and is_type_checking_test(child.test):
                continue
            if isinstance(child, (ast.Import, ast.ImportFrom)):
                body = getattr(node, "body", [])
                direct = child in body if isinstance(body, list) else False
                hits.append((child, owner if direct else None))
                continue
            next_owner = (
                child
                if isinstance(
                    child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
                )
                else None
            )
            walk(child, next_owner)

    for stmt in tree.body:
        if isinstance(stmt, (ast.Import, ast.ImportFrom)):
            continue
        if isinstance(stmt, ast.If) and is_type_checking_test(stmt.test):
            continue
        if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            walk(stmt, stmt)
        else:
            walk(stmt, None)
    hits.sort(key=lambda item: (item[0].lineno, item[0].col_offset))
    return hits


def is_exempt(lines: list[str], node: ast.stmt) -> bool:
    """导入语句行尾或上一行带 lazy-import 标记时豁免"""
    first = node.lineno - 1
    if MARKER.search("\n".join(lines[first : node.end_lineno])):
        return True
    return first > 0 and MARKER.search(lines[first - 1]) is not None


def render_import(node: ast.stmt) -> str | None:
    """把导入语句渲染成单行源码，多名字或多行写法返回 None 交给人工处理"""
    if isinstance(node, ast.Import):
        if len(node.names) != 1:
            return None
        alias = node.names[0]
        return f"import {alias.name}" + (f" as {alias.asname}" if alias.asname else "")

    if not isinstance(node, ast.ImportFrom) or len(node.names) != 1:
        return None
    alias = node.names[0]
    dots = "." * node.level
    module = f"{dots}{node.module}" if node.module else dots
    name = f"{alias.name} as {alias.asname}" if alias.asname else alias.name
    return f"from {module} import {name}"


def import_group(node: ast.stmt) -> int:
    """导入分组：标准库、第三方、app 与相对导入"""
    if isinstance(node, ast.ImportFrom) and node.level:
        return GROUP_FIRST_PARTY
    module = node.module if isinstance(node, ast.ImportFrom) else node.names[0].name
    root = module.split(".")[0] if module else ""
    if root in FIRST_PARTY_ROOTS:
        return GROUP_FIRST_PARTY
    return GROUP_STDLIB if root in STDLIB else GROUP_THIRD_PARTY


def sort_key(node: ast.stmt) -> tuple[int, str, int, str]:
    """组内排序键：相对导入排在绝对导入之后，同模块内 import 先于 from import"""
    if isinstance(node, ast.ImportFrom):
        relative = 1 if node.level else 0
        module = (node.module or "").lower()
        return (relative, module, 1, ",".join(item.name.lower() for item in node.names))
    return (0, node.names[0].name.lower(), 0, "")


def top_imports(tree: ast.Module) -> list[ast.stmt]:
    """文件顶层的导入语句"""
    return [
        node for node in tree.body if isinstance(node, (ast.Import, ast.ImportFrom))
    ]


def fallback_anchor(tree: ast.Module) -> tuple[int, str]:
    """文件里没有任何顶层导入时的插入位置，跳过模块文档字符串"""
    if tree.body:
        first = tree.body[0]
        if (
            isinstance(first, ast.Expr)
            and isinstance(first.value, ast.Constant)
            and isinstance(first.value.value, str)
        ):
            return first.end_lineno or first.lineno, SEP_AFTER
    return 0, SEP_AFTER


def insert_position(
    tree: ast.Module, existing: list[ast.stmt], group: int, key: tuple
) -> tuple[int, str]:
    """计算插入行下标与分隔空行方向"""
    same = [node for node in existing if import_group(node) == group]
    if same:
        same.sort(key=sort_key)
        for node in same:
            if key < sort_key(node):
                return node.lineno - 1, SEP_NONE
        return same[-1].end_lineno, SEP_NONE

    higher = [node for node in existing if import_group(node) > group]
    if higher:
        first = min(higher, key=lambda node: node.lineno)
        return first.lineno - 1, SEP_AFTER

    lower = [node for node in existing if import_group(node) < group]
    if lower:
        last = max(lower, key=lambda node: node.end_lineno)
        return last.end_lineno, SEP_BEFORE

    return fallback_anchor(tree)


def deletion_range(node: ast.stmt, lines: list[str]) -> tuple[int, int]:
    """删除区间，顺带吃掉语句上方的空行，避免函数体里留下双空行"""
    start, end = node.lineno - 1, node.end_lineno
    if start > 0 and not lines[start - 1].strip():
        start -= 1
    return start, end


def blank_lines_after(lines: list[str], index: int) -> int:
    """统计插入点之后连续的空行数"""
    count = 0
    while index + count < len(lines) and not lines[index + count].strip():
        count += 1
    return count


def blank_padding(lines: list[str], index: int) -> int:
    """插入的导入块与下方内容之间保留的空行数，紧邻顶层定义时按 PEP8 空两行"""
    while index < len(lines) and not lines[index].strip():
        index += 1
    if index >= len(lines):
        return 0
    head = lines[index]
    return 2 if head.startswith(("def ", "async def ", "class ", "@")) else 1


def analyze_source(
    source: str,
) -> tuple[str, list[tuple[int, str]], list[tuple[int, str]]]:
    """返回（整理后的源码，已上移的（行号，语句），需人工处理的（行号，原因））"""
    tree = parse_source(source)
    if tree is None:
        return source, [], []

    lines = source.split("\n")
    if lines and lines[-1] == "":
        lines = lines[:-1]

    existing = top_imports(tree)
    rendered = {text for node in existing if (text := render_import(node)) is not None}

    deletions: list[tuple[int, int]] = []
    insertions: dict[int, list[tuple[tuple, str, str]]] = {}
    moved: list[tuple[int, str]] = []
    skipped: list[tuple[int, str]] = []

    for node, owner in nested_imports(tree):
        if is_exempt(lines, node):
            continue

        if owner is None:
            skipped.append(
                (node.lineno, "位于条件分支内，上移会改变执行条件，需人工处理")
            )
            continue
        text = render_import(node)
        if text is None:
            skipped.append((node.lineno, "多行或多名字导入，需人工移到文件顶部"))
            continue
        if len(text) > LINE_LENGTH:
            skipped.append((node.lineno, "上移后超过行宽限制，需人工处理"))
            continue
        raw = lines[node.lineno - 1] if node.lineno <= len(lines) else ""
        if "#" in raw:
            skipped.append((node.lineno, "带行尾注释，需人工移到文件顶部"))
            continue

        deletions.append(deletion_range(node, lines))
        moved.append((node.lineno, text))
        if text in rendered:
            continue
        rendered.add(text)
        anchor, separator = insert_position(
            tree, existing, import_group(node), sort_key(node)
        )
        insertions.setdefault(anchor, []).append((sort_key(node), separator, text))

    edits: list[tuple[int, int, list[str]]] = [
        (start, end, []) for start, end in deletions
    ]
    for anchor, entries in insertions.items():
        entries.sort(key=lambda item: item[0])
        separator = entries[0][1]
        anchor = min(anchor, len(lines))
        block: list[str] = []
        if separator == SEP_BEFORE:
            block.append("")
        block.extend(text for _, _, text in entries)
        end = anchor
        if separator == SEP_AFTER:
            # 收掉插入点原有的空行后按下方内容补足，避免出现连续多行空白
            end = anchor + blank_lines_after(lines, anchor)
            block.extend([""] * blank_padding(lines, end))
        edits.append((anchor, end, block))

    edits.sort(key=lambda item: item[0], reverse=True)
    result = list(lines)
    for start, end, block in edits:
        result[start:end] = block
    return "\n".join(result) + "\n", moved, skipped


def analyze(path: Path, source: str) -> tuple[list[Finding], str]:
    """返回（问题列表，整理后的源码）"""
    fixed, moved, skipped = analyze_source(source)
    findings = [
        Finding(path=path, line=line, message=f"{text} 应移到文件顶部")
        for line, text in moved
    ]
    findings.extend(
        Finding(path=path, line=line, message=reason) for line, reason in skipped
    )
    return findings, fixed


def main() -> int:
    parser = argparse.ArgumentParser(description="模块级导入规范检查与整理")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true", help="只检查不修改文件")
    group.add_argument("--fix", action="store_true", help="自动上移可整理的导入")
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
            fixed, moved, _ = analyze_source(source)
            if not moved or fixed == source:
                continue
            with path.open("w", encoding="utf-8", newline="\n") as handle:
                handle.write(fixed)
            print(f"[FIXED] {path} 已把 {len(moved)} 处导入移到文件顶部")

    failed = False
    for path in files:
        try:
            source = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        findings, _ = analyze(path, source)
        for finding in findings:
            prefix = "[ERROR]" if args.check else "[ERROR] 未修复"
            print(f"{prefix} {finding.describe()}")
            failed = True

    if failed:
        print(
            "[ERROR] 存在不符合模块级导入规范的文件：import 一律写在文件顶部，"
            "循环依赖或确需延迟加载的导入在语句行尾或上一行写 # lazy-import: 原因"
        )
        return 1

    print(
        "[INFO] 模块级导入规范检查通过"
        if args.check
        else "[INFO] 模块级导入规范整理完成"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

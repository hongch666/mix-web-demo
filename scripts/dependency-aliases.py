#!/usr/bin/env python3
"""依赖别名规范检查与整理

规范：文件内顺序固定为「装配函数 → 依赖别名」
  - 装配函数（provide_xxx / resolve_xxx）写在前面
  - 依赖别名（XxxDep = Annotated[T, Depends(...)]，含 DbSession 这类会话别名）
    集中构成文件末尾的连续区块，首个别名之后不再出现任何函数或其它语句
  - 区块内部保持原有间距：仓库现状是紧邻连续书写，不插空行，也不与上方语句挤在一起

原因：别名与装配函数交错时，改一处别名要在两段之间来回找；
集中到末尾后，文件读起来就是「怎么装配 → 有哪些可注入的依赖」。

配套约束：装配函数的参数不能引用本文件定义的别名，因为别名在末尾，而 Python 在 def
时即对注解求值，会退化成前向引用。需要注入另一个服务的实例时写内联
Annotated[XxxService, Depends(provide_xxx_service)]。这类引用无法自动改写，只能人工处理，
脚本会报出具体位置并跳过该文件的整理。

用法：
  python scripts/dependency-aliases.py --check <路径...>
  python scripts/dependency-aliases.py --fix <路径...>

路径可以是文件或目录，目录下递归收集 .py 文件
退出码：0 通过，1 存在不符合项或整理失败
"""

from __future__ import annotations

import argparse
import ast
import sys
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

SKIP_DIRS = {".venv", "__pycache__", ".ruff_cache", ".pytest_cache"}


@dataclass(frozen=True)
class Finding:
    """一处不符合规范的依赖声明"""

    path: Path
    line: int
    message: str

    def describe(self) -> str:
        return f"{self.path}:{self.line} {self.message}"


@dataclass(frozen=True)
class AliasChunk:
    """一个依赖别名的源码区间，start / end 为 0-based 半开区间"""

    start: int
    end: int
    name: str


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


def is_annotated(value: ast.expr) -> bool:
    """判断表达式是否为 Annotated[...] 下标"""
    if not isinstance(value, ast.Subscript):
        return False
    head = value.value
    if isinstance(head, ast.Name):
        return head.id == "Annotated"
    return isinstance(head, ast.Attribute) and head.attr == "Annotated"


def is_depends_call(node: ast.expr) -> bool:
    """判断表达式是否为 Depends(...) 调用"""
    if not isinstance(node, ast.Call):
        return False
    func = node.func
    if isinstance(func, ast.Name):
        return func.id == "Depends"
    return isinstance(func, ast.Attribute) and func.attr == "Depends"


def is_alias_node(node: ast.stmt) -> bool:
    """判断模块级语句是否为依赖别名声明，形如 Name = Annotated[T, Depends(...)]"""
    if not isinstance(node, ast.Assign) or len(node.targets) != 1:
        return False
    if not isinstance(node.targets[0], ast.Name):
        return False
    if not is_annotated(node.value):
        return False
    return any(is_depends_call(item) for item in ast.walk(node.value))


def node_start(node: ast.stmt) -> int:
    """语句的起始行下标，带装饰器的定义以第一个装饰器为准"""
    decorators = getattr(node, "decorator_list", [])
    first = node.lineno
    if decorators:
        first = min(first, min(item.lineno for item in decorators))
    return first - 1


def alias_chunks(tree: ast.Module, lines: list[str]) -> list[AliasChunk]:
    """收集全部依赖别名的源码区间，紧邻上方的注释随别名一起搬走"""
    chunks: list[AliasChunk] = []
    for node in tree.body:
        if not is_alias_node(node):
            continue
        start, end = node.lineno - 1, node.end_lineno
        while start > 0 and lines[start - 1].strip().startswith("#"):
            start -= 1
        name = node.targets[0].id
        chunks.append(AliasChunk(start, end, name))
    return chunks


def collapse_blank_runs(lines: list[str], limit: int = 2) -> list[str]:
    """把连续空行压缩到指定条数，避免搬走别名后留下大段空白"""
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


def is_trailing_group(tree: ast.Module, chunks: list[AliasChunk], lines: list[str]) -> bool:
    """别名是否已经构成文件末尾的连续区块，是则无需整理"""
    if not chunks:
        return True
    first = chunks[0].start
    for node in tree.body:
        if is_alias_node(node):
            continue
        if node_start(node) >= first:
            return False
    tail = lines[chunks[-1].end :]
    return all(not line.strip() or line.strip().startswith("#") for line in tail)


def reorder(source: str) -> str:
    """把全部依赖别名搬到文件末尾，其余内容与别名区块内部的间距保持原样"""
    lines = source.split("\n")
    if lines and lines[-1] == "":
        lines = lines[:-1]

    tree = parse_source(source)
    if tree is None:
        return source
    chunks = alias_chunks(tree, lines)
    if not chunks or is_trailing_group(tree, chunks, lines):
        return source

    removed: set[int] = set()
    for chunk in chunks:
        removed.update(range(chunk.start, chunk.end))
    rest = [line for index, line in enumerate(lines) if index not in removed]
    rest = collapse_blank_runs(rest)
    while rest and not rest[-1].strip():
        rest.pop()

    block: list[str] = []
    for index, chunk in enumerate(chunks):
        if index:
            # 别名之间原本只隔空行或注释时照搬，隔着函数定义则直接紧邻
            gap = lines[chunks[index - 1].end : chunk.start]
            if all(not line.strip() or line.strip().startswith("#") for line in gap):
                block.extend(gap)
        block.extend(lines[chunk.start : chunk.end])
    block = collapse_blank_runs(block)
    while block and not block[0].strip():
        block.pop(0)

    result = rest + (["", ""] if rest else []) + block
    return "\n".join(result) + "\n"


def alias_references(tree: ast.Module, chunks: list[AliasChunk]) -> list[tuple[int, str, str]]:
    """找出引用了本文件别名的装配函数，返回（行号，函数名，别名）"""
    names = {chunk.name for chunk in chunks}
    hits: list[tuple[int, str, str]] = []
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for item in ast.walk(node):
            if isinstance(item, ast.Name) and item.id in names:
                hits.append((node.lineno, node.name, item.id))
                break
    return hits


def misplaced_aliases(
    tree: ast.Module, chunks: list[AliasChunk]
) -> list[tuple[AliasChunk, int]]:
    """找出后面还有其他定义的别名，返回（别名区间，其后第一处语句行号）"""
    following = [
        node_start(node) for node in tree.body if not is_alias_node(node)
    ]

    misplaced: list[tuple[AliasChunk, int]] = []
    for chunk in chunks:
        later = [index for index in following if index >= chunk.end]
        if later:
            misplaced.append((chunk, min(later) + 1))
    return misplaced


def analyze(path: Path, source: str) -> tuple[list[Finding], str, bool]:
    """返回（问题列表，整理后的源码，是否可自动整理）"""
    tree = parse_source(source)
    if tree is None:
        return [], source, True

    lines = source.split("\n")
    chunks = alias_chunks(tree, lines)
    if not chunks:
        return [], source, True

    references = alias_references(tree, chunks)
    findings = [
        Finding(
            path=path,
            line=line,
            message=(
                f"装配函数 {name} 引用了本文件的依赖别名 {alias}，"
                "别名集中到末尾后会变成前向引用，请改为内联 "
                "Annotated[类型, Depends(provider)]"
            ),
        )
        for line, name, alias in references
    ]
    findings.extend(
        Finding(
            path=path,
            line=chunk.start + 1,
            message=(
                f"依赖别名 {chunk.name} 应与其它依赖别名一起集中写在文件末尾，"
                f"第 {line} 行起的定义应排在它之前"
            ),
        )
        for chunk, line in misplaced_aliases(tree, chunks)
    )
    return findings, reorder(source), not references


def main() -> int:
    parser = argparse.ArgumentParser(description="依赖别名规范检查与整理")
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
            findings, fixed, fixable = analyze(path, source)
            if not findings or fixed == source or not fixable:
                continue
            with path.open("w", encoding="utf-8", newline="\n") as handle:
                handle.write(fixed)
            print(f"[FIXED] {path} 已把 {len(findings)} 个依赖别名整理到文件末尾")

    failed = False
    for path in files:
        try:
            source = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        findings, _, _ = analyze(path, source)
        for finding in findings:
            prefix = "[ERROR]" if args.check else "[ERROR] 未修复"
            print(f"{prefix} {finding.describe()}")
            failed = True

    if failed:
        print(
            "[ERROR] 存在不符合依赖别名规范的文件：装配函数写在前、依赖别名集中在末尾，"
            "位置问题可用 ./mix format 自动整理；装配函数引用本文件别名的需人工改为内联"
        )
        return 1

    print(
        "[INFO] 依赖别名规范检查通过"
        if args.check
        else "[INFO] 依赖别名规范整理完成"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

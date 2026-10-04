#!/usr/bin/env python3
"""包导入规范检查与整理

规范一：目标模块所在的目录已经通过 __init__.py 导出某个成员时，
引用方应当从包导入（from pkg import name），不要直接指向具体文件
（from pkg.mod import name）。

适用范围与例外：
  - 目标目录没有 __init__.py 时该规范不适用
  - __init__.py 用 from .mod import name 重导出属于必要写法，不算违规
  - 与目标同属一个包的引用不做要求：包内互相引用走文件更自然
  - 导入方位于目标包 __init__.py 的导入链上时不做要求：改成包导入会构成循环导入
  判定口径：__init__.py 在模块级绑定了被引用的全部名字（含 from 导入重导出、
  赋值、类与函数定义），即视为已导出。

规范二：模块级 from ... import ... 需要归一
  - 同一目标（相同相对层级与模块）的多条语句合并为一条
  - 导入的名字按字典序排列（ASCII 序，与 isort 的大小写敏感默认一致）
  - 通配导入 from x import * 所在的组不参与合并与排序

用法：
  python scripts/package-imports.py --check <路径...>
  python scripts/package-imports.py --fix <路径...>

路径可以是文件或目录，目录下递归收集 .py 文件，且目录本身作为导入根
退出码：0 通过，1 存在不符合项或整理失败
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path

SKIP_DIRS = {".venv", "__pycache__", ".ruff_cache", ".pytest_cache"}
# 与 pyproject.toml 的 ruff line-length 保持一致，超出则改用括号多行写法
LINE_LENGTH = 88
IMPORT_STATEMENT = re.compile(
    r"^(?P<indent>\s*from\s+)(?P<dots>\.*)(?P<module>[\w.]*)(?P<rest>\s+import\s+.*)$"
)
TRAILING_COMMENT = re.compile(r"\s+#.*$")


@dataclass(frozen=True)
class Fix:
    """一处行区间改写，start / end 为 1-based 闭区间，lines 为空表示删除该区间"""

    start: int
    end: int
    lines: tuple[str, ...] = ()


@dataclass(frozen=True)
class Finding:
    """一处不符合规范的引用"""

    path: Path
    line: int
    message: str
    fix: Fix | None = None

    def describe(self) -> str:
        return f"{self.path}:{self.line} {self.message}"


@dataclass
class Index:
    """仓库内的模块索引与缓存"""

    # 点分模块路径 -> 模块文件
    modules: dict[str, Path] = field(default_factory=dict)
    # 点分包路径 -> __init__.py
    packages: dict[str, Path] = field(default_factory=dict)
    # 文件 -> 点分路径（模块或包）
    dotted: dict[Path, str] = field(default_factory=dict)
    # 文件 -> 直接导入的仓库内文件
    edges: dict[Path, frozenset[Path]] = field(default_factory=dict)
    # 文件 -> 从该文件可达的文件集合
    reachable: dict[Path, frozenset[Path]] = field(default_factory=dict)
    # __init__.py -> 已导出的名字
    exported: dict[Path, frozenset[str]] = field(default_factory=dict)

    def package_of(self, path: Path) -> str:
        """文件所属包的点分路径，顶层脚本返回空串"""
        dotted = self.dotted.get(path)
        if dotted is None:
            return ""
        if path.name == "__init__.py":
            return dotted
        return dotted.rpartition(".")[0]

    def file_of(self, dotted: str) -> Path | None:
        """点分路径对应的文件，模块与包都支持"""
        return self.modules.get(dotted) or self.packages.get(dotted)


def iter_python_files(root: Path) -> Iterator[Path]:
    for item in sorted(root.rglob("*.py")):
        if any(part in SKIP_DIRS for part in item.parts):
            continue
        yield item


def collect_files(paths: list[str]) -> list[Path]:
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


def build_index(roots: list[Path]) -> Index:
    index = Index()
    for root in roots:
        for file in iter_python_files(root):
            parts = list(file.relative_to(root).with_suffix("").parts)
            if parts[-1] == "__init__":
                if len(parts) == 1:
                    # 根目录自身就是包的 __init__.py，没有可用的点分前缀
                    continue
                name = ".".join(parts[:-1])
                index.packages[name] = file
                index.dotted[file] = name
            else:
                name = ".".join(parts)
                index.modules[name] = file
                index.dotted[file] = name
    return index


def parse_source(source: str) -> ast.Module | None:
    try:
        return ast.parse(source)
    except (SyntaxError, ValueError):
        return None


def parse_file(path: Path) -> ast.Module | None:
    try:
        return parse_source(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError):
        return None


def resolve_module(
    node: ast.ImportFrom, own_package: str
) -> tuple[str, str, str] | None:
    """解析导入语句的目标

    返回（目标模块点分路径，目标所在包点分路径，相对导入的基准包），
    绝对导入的基准包为空串
    """
    if node.level:
        if not own_package:
            return None
        parts = own_package.split(".")
        if len(parts) < node.level:
            return None
        base = ".".join(parts[: len(parts) - node.level + 1])
        module = f"{base}.{node.module}" if node.module else base
        return module, module.rpartition(".")[0], base

    module = node.module
    if module is None:
        return None
    package = module.rpartition(".")[0]
    if not package:
        return None
    return module, package, ""


def target_names(target: ast.expr) -> set[str]:
    """取出赋值目标上的名字"""
    if isinstance(target, ast.Name):
        return {target.id}
    if isinstance(target, (ast.Tuple, ast.List)):
        names: set[str] = set()
        for element in target.elts:
            names |= target_names(element)
        return names
    return set()


def bound_names(body: list[ast.stmt]) -> set[str]:
    """收集一段语句块在模块级绑定的名字"""
    names: set[str] = set()
    for node in body:
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                if alias.name != "*":
                    names.add(alias.asname or alias.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.asname or alias.name.split(".")[0])
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                names |= target_names(target)
        elif isinstance(node, ast.AnnAssign):
            names |= target_names(node.target)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, ast.Try):
            names |= bound_names(node.body)
            names |= bound_names(node.orelse)
            names |= bound_names(node.finalbody)
            for handler in node.handlers:
                names |= bound_names(handler.body)
        elif isinstance(node, ast.If):
            names |= bound_names(node.body)
            names |= bound_names(node.orelse)
        elif isinstance(node, (ast.With, ast.AsyncWith)):
            names |= bound_names(node.body)
    return names


def exported_names(index: Index, init_file: Path) -> frozenset[str]:
    """读取包 __init__.py 已导出的名字"""
    if init_file not in index.exported:
        tree = parse_file(init_file)
        index.exported[init_file] = (
            frozenset(bound_names(tree.body)) if tree is not None else frozenset()
        )
    return index.exported[init_file]


def import_edges(index: Index, path: Path) -> frozenset[Path]:
    """文件直接导入的仓库内文件集合"""
    if path in index.edges:
        return index.edges[path]

    targets: set[Path] = set()
    tree = parse_file(path)
    if tree is not None:
        own_package = index.package_of(path)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                resolved = resolve_module(node, own_package)
                dotted = resolved[0] if resolved else None
            elif isinstance(node, ast.Import):
                dotted = node.names[0].name if node.names else None
            else:
                continue
            if not dotted:
                continue
            target = index.file_of(dotted)
            if target is not None:
                targets.add(target)

    index.edges[path] = frozenset(targets)
    return index.edges[path]


def reachable_files(index: Index, start: Path) -> frozenset[Path]:
    """从某个文件出发可到达的仓库内文件集合"""
    if start in index.reachable:
        return index.reachable[start]

    seen: set[Path] = set()
    stack = [start]
    while stack:
        for target in import_edges(index, stack.pop()):
            if target not in seen:
                seen.add(target)
                stack.append(target)

    index.reachable[start] = frozenset(seen)
    return index.reachable[start]


def package_import_findings(index: Index, path: Path, source: str) -> list[Finding]:
    """规范一：应改为从包导入的引用"""
    tree = parse_source(source)
    if tree is None:
        return []

    own_package = index.package_of(path)
    lines = source.split("\n")
    findings: list[Finding] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ImportFrom):
            continue

        resolved = resolve_module(node, own_package)
        if resolved is None:
            continue
        module, package, base = resolved

        # 只约束“模块文件”；目标本身是包时不属于本规范
        if module not in index.modules:
            continue
        if not package or package == own_package:
            continue
        init_file = index.packages.get(package)
        if init_file is None:
            continue

        names = tuple(alias.name for alias in node.names if alias.name != "*")
        if not names:
            continue
        if not set(names).issubset(exported_names(index, init_file)):
            continue
        # 导入方在目标包的导入链上时，改成包导入会构成循环导入
        if path in reachable_files(index, init_file):
            continue

        dots = "." * node.level
        module_text = package[len(base) + 1 :] if base else package
        matched = IMPORT_STATEMENT.match(lines[node.lineno - 1])
        if matched is None:
            continue
        rewritten = (
            f"{matched.group('indent')}{dots}{module_text}{matched.group('rest')}"
        )
        findings.append(
            Finding(
                path=path,
                line=node.lineno,
                message=(
                    f"直接引用了文件模块 {module}，"
                    f"应改为从包导入：from {dots}{module_text} import {', '.join(names)}"
                ),
                fix=Fix(node.lineno, node.lineno, (rewritten,)),
            )
        )
    return findings


def render_import(
    level: int, module: str | None, aliases: list[tuple[str, str | None]]
) -> str:
    """渲染一条 from 导入语句，超长时改为括号多行"""
    dots = "." * level
    head = f"from {dots}{module} import " if module else f"from {dots} import "
    rendered = [
        f"{name} as {asname}" if asname else name for name, asname in aliases
    ]
    one_line = head + ", ".join(rendered)
    if len(one_line) <= LINE_LENGTH:
        return one_line
    body = "\n".join(f"    {item}," for item in rendered)
    return f"{head}(\n{body}\n)"


def merge_sort_findings(path: Path, source: str) -> list[Finding]:
    """规范二：模块级 from 导入的合并与名字排序"""
    tree = parse_source(source)
    if tree is None:
        return []

    lines = source.split("\n")
    groups: dict[tuple[int, str | None], list[ast.ImportFrom]] = {}
    for node in tree.body:
        if isinstance(node, ast.ImportFrom):
            groups.setdefault((node.level, node.module), []).append(node)

    findings: list[Finding] = []
    for (level, module), nodes in groups.items():
        nodes.sort(key=lambda item: item.lineno)
        # 通配导入的顺序有语义，所在组整体跳过
        if any(alias.name == "*" for node in nodes for alias in node.names):
            continue
        # 语句内部带注释时无法安全重排，整组跳过
        if any(
            "#" in line
            for node in nodes
            for line in lines[node.lineno - 1 : node.end_lineno - 1]
        ):
            continue
        # 行尾注释（如 noqa）需要保留，多处则合并会丢信息，整组跳过
        comments = [
            TRAILING_COMMENT.search(lines[node.end_lineno - 1]) for node in nodes
        ]
        if sum(1 for matched in comments if matched) > 1:
            continue
        comment = next(
            (matched.group(0) for matched in comments if matched is not None), ""
        )

        merged: list[tuple[str, str | None]] = []
        seen: set[tuple[str, str | None]] = set()
        for node in nodes:
            for alias in node.names:
                key = (alias.name, alias.asname)
                if key not in seen:
                    seen.add(key)
                    merged.append(key)
        merged.sort(key=lambda item: (item[0], item[1] or ""))
        rendered_lines = render_import(level, module, merged).split("\n")
        rendered_lines[-1] += comment
        rendered = "\n".join(rendered_lines)

        target = module or "." * level
        first = nodes[0]
        current = "\n".join(lines[first.lineno - 1 : first.end_lineno])
        if len(nodes) == 1 and current == rendered:
            continue

        if len(nodes) == 1:
            message = f"从 {target} 导入的名字未按字典序排列"
        elif current == rendered:
            message = f"从 {target} 的重复导入可合并为一条语句"
        else:
            message = f"从 {target} 的重复导入可合并为一条语句并按字典序排列"
        findings.append(
            Finding(
                path=path,
                line=first.lineno,
                message=message,
                fix=Fix(first.lineno, first.end_lineno, tuple(rendered.split("\n"))),
            )
        )

        for node in nodes[1:]:
            start, end = node.lineno, node.end_lineno
            # 删除语句后若上下都留空行，顺带去掉多余的一行
            if (
                start - 2 >= 0
                and end < len(lines)
                and lines[start - 2].strip() == ""
                and lines[end].strip() == ""
            ):
                end += 1
            findings.append(
                Finding(
                    path=path,
                    line=node.lineno,
                    message=f"与第 {first.lineno} 行的导入重复，可删除",
                    fix=Fix(start, end, ()),
                )
            )
    return findings


def apply_fixes(source: str, findings: list[Finding]) -> str:
    """按行区间从后往前应用改写"""
    lines = source.split("\n")
    fixes = [finding.fix for finding in findings if finding.fix is not None]
    for fix in sorted(fixes, key=lambda item: item.start, reverse=True):
        lines[fix.start - 1 : fix.end] = list(fix.lines)
    return "\n".join(lines)


def analyze(index: Index, path: Path, source: str) -> tuple[list[Finding], str]:
    """返回（问题列表，整理后的源码）

    先按规范一改写，再在改写结果上按规范二合并与排序；
    规范一只替换行内容、不增删行，两阶段的报错行号都可用
    """
    findings = package_import_findings(index, path, source)
    rewritten = apply_fixes(source, findings)
    merge_findings = merge_sort_findings(path, rewritten)
    return findings + merge_findings, apply_fixes(rewritten, merge_findings)


def main() -> int:
    parser = argparse.ArgumentParser(description="包导入规范检查与整理")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true", help="只检查不修改文件")
    group.add_argument("--fix", action="store_true", help="自动改写不符合的文件")
    parser.add_argument("paths", nargs="+", help="待检查或整理的文件与目录")
    args = parser.parse_args()

    try:
        files = collect_files(args.paths)
    except FileNotFoundError as error:
        print(f"[ERROR] 路径不存在: {error}")
        return 1

    # 以每个传入目录自身作为导入根，导入根下的点分路径即可解析
    roots = [Path(raw) for raw in args.paths if Path(raw).is_dir()]
    index = build_index(roots)

    if args.fix:
        for path in files:
            try:
                source = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            findings, fixed = analyze(index, path, source)
            if not findings or fixed == source:
                continue
            with path.open("w", encoding="utf-8", newline="\n") as handle:
                handle.write(fixed)
            print(f"[FIXED] {path} 已整理 {len(findings)} 处导入")
        # 改写后重建索引，复查是否还有残留
        index = build_index(roots)

    failed = False
    for path in files:
        try:
            source = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        findings, _ = analyze(index, path, source)
        for finding in findings:
            prefix = "[ERROR]" if args.check else "[ERROR] 未修复"
            print(f"{prefix} {finding.describe()}")
            failed = True

    if failed:
        print(
            "[ERROR] 存在不符合包导入规范的文件：从包导入的目标目录没有 "
            "__init__.py、与目标同包或位于目标包导入链上时不受约束，"
            "重复导入与名字排序可用 ./mix format 自动整理"
        )
        return 1

    print("[INFO] 包导入规范检查通过" if args.check else "[INFO] 包导入规范整理完成")
    return 0


if __name__ == "__main__":
    sys.exit(main())

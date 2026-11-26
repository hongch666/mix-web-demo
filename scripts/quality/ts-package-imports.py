#!/usr/bin/env python3
"""TypeScript 包导入规范检查与整理

规范一：目标文件所在目录已经通过 index.ts 导出某个成员时
引用方应当从目录入口导入（from "src/common/utils"），不要直接指向具体文件
（from "src/common/utils/snakeCase"）

适用范围与例外：
  - 目标目录没有 index.ts 时该规范不适用
  - index.ts 用 export ... from "./mod" 重导出属于必要写法，不算违规
  - 与目标同目录的引用不做要求，包内实现互引走相对路径更自然
  - 导入方位于目标 index.ts 的导入链上时不做要求，改成入口导入会构成循环导入
  - 副作用导入（import "xxx"）不在本规范约束范围内
  判定口径：index.ts 在模块级导出了被引用的全部名字，即视为已导出

规范二：模块级具名 import 需要归一
  - 同一目标的多个语句合并为一条，名字按首次出现顺序保留
  - 类型导入与值导入分开处理，不跨类型合并
  - 带行内注释的语句只报位置，不自动改写

用法：
  python scripts/quality/ts-package-imports.py --check <路径...>
  python scripts/quality/ts-package-imports.py --fix <路径...>

路径可以是文件或目录，目录下递归收集 src 中的 .ts 文件
退出码：0 通过，1 存在不符合项或整理失败
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

SKIP_DIRS = {"node_modules", "dist", "coverage", ".git"}
BARREL_NAME = "index.ts"
PRINT_WIDTH = 80
NAMED_IMPORT = re.compile(
    r'(?m)^(?P<indent>[ \t]*)import\s+(?P<type>type\s+)?\{'
    r'(?P<names>[^}]*)\}\s+from\s+(?P<quote>["\'])'
    r'(?P<spec>[^"\']+)(?P=quote);'
)
FROM_SPEC = re.compile(r'\bfrom\s+(["\'])([^"\']+)\1')
SIDE_IMPORT = re.compile(r'(?m)^[ \t]*import\s+(["\'])([^"\']+)\1')
EXPORT_NAMED = re.compile(
    r'\bexport\s+(type\s+)?\{([^}]*)\}\s+from\s+["\'][^"\']+["\']'
)
EXPORT_DECL = re.compile(
    r'\bexport\s+(?:declare\s+)?(?:abstract\s+)?(?:async\s+)?'
    r'(?:class|interface|type|enum|const|let|var|function)\s+'
    r'([A-Za-z_$][\w$]*)'
)


@dataclass(frozen=True)
class Fix:
    """一处行区间改写，start / end 为 1-based 闭区间，lines 为空表示删除"""

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
    """仓库内的文件索引与缓存"""

    root: Path
    src_root: Path
    files: list[Path] = field(default_factory=list)
    barrels: dict[Path, Path] = field(default_factory=dict)
    exported: dict[Path, frozenset[str]] = field(default_factory=dict)
    edges: dict[Path, frozenset[Path]] = field(default_factory=dict)
    reachable: dict[Path, frozenset[Path]] = field(default_factory=dict)

    def alias(self, target: Path) -> str:
        """目标目录对应的 src/ 别名"""
        return "src/" + target.relative_to(self.src_root).as_posix()


def iter_ts_files(src_root: Path) -> list[Path]:
    files: list[Path] = []
    for item in sorted(src_root.rglob("*.ts")):
        if item.name.endswith(".d.ts"):
            continue
        if any(part in SKIP_DIRS for part in item.parts):
            continue
        files.append(item)
    return files


def find_service_root(path: Path) -> Path:
    """从文件或目录向上找到包含 src 的服务根目录"""
    current = path.resolve()
    candidates = [current, *current.parents]
    for candidate in candidates:
        if (candidate / "src").is_dir():
            return candidate
    return current if current.is_dir() else current.parent


def collect_files(paths: list[str]) -> tuple[list[Path], list[Path]]:
    files: list[Path] = []
    roots: list[Path] = []
    seen_files: set[Path] = set()
    seen_roots: set[Path] = set()
    for raw in paths:
        path = Path(raw)
        if not path.exists():
            raise FileNotFoundError(raw)
        root = find_service_root(path)
        src_root = root / "src"
        if src_root not in seen_roots:
            seen_roots.add(src_root)
            roots.append(root)
        if path.is_dir():
            candidates = iter_ts_files(src_root)
        else:
            candidates = [path.resolve()] if path.suffix == ".ts" else []
        for item in candidates:
            if item not in seen_files:
                seen_files.add(item)
                files.append(item)
    return files, roots


def read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def split_names(raw: str) -> list[str]:
    """拆出具名导入条目，保留别名与 inline type 修饰"""
    return [item.strip() for item in raw.split(",") if item.strip()]


def name_of(item: str) -> str:
    """取导入条目的原始名字，去掉 type 修饰与 as 别名"""
    cleaned = re.sub(r"^type\s+", "", item.strip())
    return cleaned.split(" as ")[0].strip()


def exported_names(path: Path) -> frozenset[str]:
    source = read_text(path)
    if source is None:
        return frozenset()
    names: set[str] = set()
    for matched in EXPORT_NAMED.finditer(source):
        for item in split_names(matched.group(2)):
            name = name_of(item)
            if name:
                names.add(name)
    for matched in EXPORT_DECL.finditer(source):
        names.add(matched.group(1))
    return frozenset(names)


def build_index(roots: list[Path]) -> Index:
    first = roots[0]
    index = Index(root=first, src_root=first / "src")
    files: list[Path] = []
    seen: set[Path] = set()
    for root in roots:
        for item in iter_ts_files(root / "src"):
            if item not in seen:
                seen.add(item)
                files.append(item)
    index.files = files
    for item in files:
        if item.name == BARREL_NAME:
            index.barrels[item.parent] = item
    for barrel in index.barrels.values():
        index.exported[barrel] = exported_names(barrel)
    return index


def resolve_spec(index: Index, origin: Path, spec: str) -> Path | None:
    if spec.startswith("src/"):
        base = index.root / spec
    elif spec.startswith("."):
        base = Path(os.path.normpath(str(origin.parent / spec)))
    else:
        return None
    candidates = [base, Path(str(base) + ".ts"), base / BARREL_NAME]
    for candidate in candidates:
        if candidate.is_file() and candidate.suffix == ".ts":
            if not candidate.name.endswith(".d.ts"):
                return candidate
    return None


def import_edges(index: Index, path: Path) -> frozenset[Path]:
    if path in index.edges:
        return index.edges[path]
    targets: set[Path] = set()
    source = read_text(path)
    if source is not None:
        specs = [matched.group(2) for matched in FROM_SPEC.finditer(source)]
        specs.extend(matched.group(2) for matched in SIDE_IMPORT.finditer(source))
        for spec in specs:
            target = resolve_spec(index, path, spec)
            if target is not None:
                targets.add(target)
    index.edges[path] = frozenset(targets)
    return index.edges[path]


def reachable_files(index: Index, start: Path) -> frozenset[Path]:
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


def render_import(spec: str, items: list[str], type_only: bool) -> str:
    head = "import " + ("type " if type_only else "") + "{"
    one_line = f"{head} {', '.join(items) } }} from \"{spec}\";"
    if len(one_line) <= PRINT_WIDTH:
        return one_line
    body = "\n".join(f"  {item}," for item in items)
    return f"{head}\n{body}\n}} from \"{spec}\";"


def package_import_findings(
    index: Index, path: Path, source: str
) -> list[Finding]:
    findings: list[Finding] = []
    for matched in NAMED_IMPORT.finditer(source):
        if matched.group("indent"):
            continue
        spec = matched.group("spec")
        target = resolve_spec(index, path, spec)
        if target is None or target.name == BARREL_NAME:
            continue
        target_dir = target.parent
        barrel = index.barrels.get(target_dir)
        if barrel is None:
            continue
        if path.name == BARREL_NAME or path.parent == target_dir:
            continue
        if path in reachable_files(index, barrel):
            continue

        items = split_names(matched.group("names"))
        names = [name_of(item) for item in items if name_of(item)]
        if not names:
            continue
        exported = index.exported.get(barrel, frozenset())
        if not set(names).issubset(exported):
            continue

        alias = index.alias(target_dir)
        if spec == alias:
            continue
        rendered = render_import(alias, items, bool(matched.group("type")))
        start = source.count("\n", 0, matched.start()) + 1
        end = start + matched.group(0).count("\n")
        findings.append(
            Finding(
                path=path,
                line=start,
                message=(
                    f"直接引用了已有 index.ts 的文件 {spec}，"
                    f"应改为从目录入口导入：{alias}"
                ),
                fix=Fix(start, end, tuple(rendered.split("\n"))),
            )
        )
    return findings


def merge_sort_findings(path: Path, source: str) -> list[Finding]:
    groups: dict[tuple[str, bool], list[re.Match[str]]] = {}
    for matched in NAMED_IMPORT.finditer(source):
        if matched.group("indent"):
            continue
        if "#" in matched.group("names"):
            continue
        key = (matched.group("spec"), bool(matched.group("type")))
        groups.setdefault(key, []).append(matched)

    findings: list[Finding] = []
    for (spec, type_only), matches in groups.items():
        items: list[str] = []
        for matched in matches:
            for item in split_names(matched.group("names")):
                if item not in items:
                    items.append(item)
        rendered = render_import(spec, items, type_only)

        first = matches[0]
        first_text = first.group(0)
        if len(matches) == 1:
            continue

        start = source.count("\n", 0, first.start()) + 1
        end = start + first_text.count("\n")
        message = f"从 {spec} 的重复导入可合并为一条语句"
        findings.append(
            Finding(
                path=path,
                line=start,
                message=message,
                fix=Fix(start, end, tuple(rendered.split("\n"))),
            )
        )

        for matched in matches[1:]:
            start = source.count("\n", 0, matched.start()) + 1
            end = start + matched.group(0).count("\n")
            findings.append(
                Finding(
                    path=path,
                    line=start,
                    message=f"与第 {source.count(chr(10), 0, first.start()) + 1} 行的导入重复，可删除",
                    fix=Fix(start, end, ()),
                )
            )
    return findings


def apply_fixes(source: str, findings: list[Finding]) -> str:
    lines = source.split("\n")
    fixes = [finding.fix for finding in findings if finding.fix is not None]
    for fix in sorted(fixes, key=lambda item: item.start, reverse=True):
        lines[fix.start - 1 : fix.end] = list(fix.lines)
    return "\n".join(lines)


def analyze(index: Index, path: Path, source: str) -> tuple[list[Finding], str]:
    findings = package_import_findings(index, path, source)
    rewritten = apply_fixes(source, findings)
    merge_findings = merge_sort_findings(path, rewritten)
    return findings + merge_findings, apply_fixes(rewritten, merge_findings)


def main() -> int:
    parser = argparse.ArgumentParser(description="TypeScript 包导入规范检查与整理")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true", help="只检查不修改文件")
    group.add_argument("--fix", action="store_true", help="自动改写不符合的文件")
    parser.add_argument("paths", nargs="+", help="待检查或整理的文件与目录")
    args = parser.parse_args()

    try:
        files, roots = collect_files(args.paths)
    except FileNotFoundError as error:
        print(f"[ERROR] 路径不存在: {error}")
        return 1

    index = build_index(roots)
    if args.fix:
        for path in files:
            source = read_text(path)
            if source is None:
                continue
            findings, fixed = analyze(index, path, source)
            if not findings or fixed == source:
                continue
            with path.open("w", encoding="utf-8", newline="\n") as handle:
                handle.write(fixed)
            print(f"[FIXED] {path} 已整理 {len(findings)} 处导入")
        index = build_index(roots)

    failed = False
    for path in files:
        source = read_text(path)
        if source is None:
            continue
        findings, _ = analyze(index, path, source)
        for finding in findings:
            prefix = "[ERROR]" if args.check else "[ERROR] 未修复"
            print(f"{prefix} {finding.describe()}")
            failed = True

    if failed:
        print(
            "[ERROR] 存在不符合包导入规范的文件：跨目录引用具体文件时，"
            "目标目录的 index.ts 必须已导出对应名字；"
            "同目录引用、barrel 自身导出实现、副作用导入与循环依赖导入不受约束，"
            "路径替换与重复导入整理可用 ./mix format nestjs 完成"
        )
        return 1

    print("[INFO] 包导入规范检查通过" if args.check else "[INFO] 包导入规范整理完成")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""常量文件规范检查

约定（spring、gozero、nestjs、fastapi 四个服务的常量文件统一执行）：
1. 函数型成员全部排在普通常量之前（只检查 nestjs 与 fastapi，
   spring 与 gozero 的常量前缀方法与常量成对书写，不参与顺序检查）
2. 每个成员必须带注释，且注释要能被 IDE 悬停展示
   - Java：成员上方 /** 单行说明 */（Javadoc）
   - NestJS：成员上方 /** 单行说明 */（JSDoc）
   - GoZero：成员上方 // 单行说明
   - FastAPI：普通常量写在成员下方的三双引号字符串（PEP 257 属性文档串），
     @staticmethod 方法写在函数体内第一行的三双引号字符串
3. 成员按分类摆放，每个成员必须归入一个分类
   - 分类注释是单行 ===== 分类名 =====（Java/TS/Go 用 //，Python 用 #）
   - 分类注释紧贴该分类首个成员上方，可与该成员的注释相邻

检查发现问题只报错并打印文件与行号，不修改文件，需按提示人工调整

用法：
  python scripts/constants.py --check <路径...>

路径可以是文件或目录，目录下按扩展名收集 .java、.ts、.go 与 .py 文件
退出码：0 通过，1 存在不符合项
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from dataclasses import dataclass, field, replace
from pathlib import Path

FUNCTION = "function"
CONSTANT = "constant"

SUFFIXES = {".java", ".ts", ".go", ".py"}

# 分类注释：// ===== 分类名 ===== 或 # ===== 分类名 =====，单行书写
SECTION_PATTERN = re.compile(
    r"^[ \t]*(?://|#|/\*)[ \t]*={3,}[ \t]*(\S.*?)[ \t]*={3,}[ \t]*(?:\*/)?[ \t]*$"
)

JAVA_CLASS_START = re.compile(r"^(?:public |final |abstract )*(?:class|interface|enum|record) (\w+)")
JAVA_CLASS_END = re.compile(r"^\}[ \t]*$")
JAVA_MEMBER = re.compile(
    r"^ {4}(?:(?:public|private|protected|static|final|abstract|synchronized) )*\w[\w<>\[\], .?]*\s+\w+\s*[=(]"
)
JAVA_CONSTRUCTOR = re.compile(r"^ {4}(?:(?:public|private|protected) )?(\w+)\s*\(")
ANNOTATION = re.compile(r"^[ \t]*@\w+")

TS_CLASS_START = re.compile(r"^(?:export )?(?:abstract )?class (\w+)")
TS_CLASS_END = re.compile(r"^\}[ \t]*$")
TS_MEMBER = re.compile(r"^ {2}(?:static )+(?:readonly )?\w+\s*[:=]")
TS_ASYNC_PREFIX = re.compile(r"^async\s+")

GO_BLOCK_START = re.compile(r"^(?:const|var)\s*\($")
GO_BLOCK_END = re.compile(r"^\)[ \t]*$")
GO_BLOCK_MEMBER = re.compile(r"^\t(\w+)\s*(?:[\w.\[\]{}*]+)?\s*=")
GO_SINGLE_MEMBER = re.compile(r"^(?:const|var)\s+(\w+)\s*(?:[\w.\[\]{}*]+)?\s*=")

PY_COMMENT = re.compile(r"^ *#")
COMMENT_LINE = {
    ".java": re.compile(r"^ *(?://|/\*|\*|\*/)"),
    ".ts": re.compile(r"^ *(?://|/\*|\*|\*/)"),
    ".go": re.compile(r"^[ \t]*//"),
    ".py": PY_COMMENT,
}
ORDER_CHECKED = {".ts", ".py"}


@dataclass(frozen=True)
class Member:
    """常量文件里的一个成员

    block_start 为该成员附带的连续注释起始行，decl 为声明行（0-based）
    """

    name: str
    kind: str
    block_start: int
    decl: int
    has_doc: bool
    section: str | None


@dataclass
class Region:
    """参与检查的一块成员区域

    members 按出现顺序排列，start 为该区域首个成员注释块的 0-based 行下标
    """

    name: str
    members: list[Member] = field(default_factory=list)
    start: int = 0


def declaration_start(lines: list[str], decl: int, lower: int) -> int:
    """向上跨过注解行，把注释定位到首个注解上方"""
    start = decl
    while start - 1 >= lower and ANNOTATION.match(lines[start - 1]):
        start -= 1
    return start


def comment_block_start(lines: list[str], decl: int, lower: int, suffix: str) -> int:
    """向上收集紧贴成员的注释行，不越过 lower"""
    pattern = COMMENT_LINE[suffix]
    start = declaration_start(lines, decl, lower)
    while start - 1 >= lower and pattern.match(lines[start - 1]):
        start -= 1
    return start


def section_above(
    lines: list[str], block_start: int, lower: int
) -> tuple[int, str | None]:
    """向上越过空行找紧邻的分类注释，返回（分类注释行下标，分类名）"""
    cursor = block_start
    while cursor - 1 >= lower and not lines[cursor - 1].strip():
        cursor -= 1
    if cursor - 1 < lower:
        return block_start, None
    matched = SECTION_PATTERN.match(lines[cursor - 1])
    if not matched:
        return block_start, None
    return cursor - 1, matched.group(1).strip()


def split_block(
    lines: list[str], start: int, decl: int, suffix: str
) -> tuple[str | None, bool]:
    """解析成员上方的注释块，返回（分类名，是否带成员注释）"""
    section: str | None = None
    has_doc = False
    for raw in lines[start:decl]:
        matched = SECTION_PATTERN.match(raw)
        if matched:
            section = matched.group(1).strip()
            continue
        if raw.strip():
            has_doc = True
    return section, has_doc


# ==================== Java ====================


def java_regions(lines: list[str]) -> list[Region]:
    regions: list[Region] = []
    index = 0
    while index < len(lines):
        matched = JAVA_CLASS_START.match(lines[index])
        if not matched:
            index += 1
            continue

        name = matched.group(1)
        class_start = index
        is_enum = "enum" in lines[index].split()
        class_end = class_start + 1
        while class_end < len(lines) and not JAVA_CLASS_END.match(lines[class_end]):
            class_end += 1

        decls: list[tuple[str, int]] = []
        for cursor in range(class_start + 1, class_end):
            raw = lines[cursor]
            if not JAVA_MEMBER.match(raw):
                continue
            constructor = JAVA_CONSTRUCTOR.match(raw)
            if constructor and constructor.group(1) == name:
                continue
            if is_enum:
                decls.append((CONSTANT, cursor))
            elif "(" in raw.split("=")[0]:
                decls.append((FUNCTION, cursor))
            else:
                decls.append((CONSTANT, cursor))

        region = build_region(name, decls, lines, class_start + 1, ".java")
        if region is not None:
            regions.append(region)
        index = class_end + 1
    return regions


# ==================== NestJS ====================


def typescript_member_kind(lines: list[str], decl: int, limit: int) -> str:
    """按赋值号右侧的首个记号判断成员是函数还是常量"""
    text = lines[decl]
    index = decl + 1
    while "=" not in text and index < limit:
        line = lines[index]
        if not line.strip() or COMMENT_LINE[".ts"].match(line):
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


def typescript_regions(lines: list[str]) -> list[Region]:
    regions: list[Region] = []
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

        decls = [
            (typescript_member_kind(lines, cursor, class_end), cursor)
            for cursor in range(class_start + 1, class_end)
            if TS_MEMBER.match(lines[cursor])
        ]
        region = build_region(matched.group(1), decls, lines, class_start + 1, ".ts")
        if region is not None:
            regions.append(region)
        index = class_end + 1
    return regions


# ==================== GoZero ====================


def go_regions(lines: list[str]) -> list[Region]:
    regions: list[Region] = []
    index = 0
    while index < len(lines):
        raw = lines[index]
        if GO_BLOCK_START.match(raw):
            block_start = index
            block_end = block_start + 1
            while block_end < len(lines) and not GO_BLOCK_END.match(lines[block_end]):
                block_end += 1
            decls = [
                (CONSTANT, cursor)
                for cursor in range(block_start + 1, block_end)
                if GO_BLOCK_MEMBER.match(lines[cursor])
            ]
            _, block_section = section_above(lines, block_start, 0)
            region = build_region(
                f"const 块（第 {block_start + 1} 行）",
                decls,
                lines,
                block_start + 1,
                ".go",
                block_section,
            )
            if region is not None:
                regions.append(region)
            index = block_end + 1
            continue

        matched = GO_SINGLE_MEMBER.match(raw)
        if matched:
            region = build_region(
                matched.group(1), [(CONSTANT, index)], lines, 0, ".go"
            )
            if region is not None:
                regions.append(region)
        index += 1
    return regions


# ==================== FastAPI ====================


def python_member_name(item: ast.stmt, line: int) -> str:
    """取 Python 成员的名称，赋值取目标名，函数取函数名"""
    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return item.name
    if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
        return item.target.id
    if isinstance(item, ast.Assign):
        for target in item.targets:
            if isinstance(target, ast.Name):
                return target.id
    return f"第 {line + 1} 行常量"


def python_docstring_below(node: ast.stmt, following: ast.stmt | None) -> bool:
    """判断赋值语句下方是否紧跟属性文档串"""
    if not isinstance(following, ast.Expr):
        return False
    value = following.value
    if not isinstance(value, ast.Constant) or not isinstance(value.value, str):
        return False
    return following.lineno == node.end_lineno + 1


def python_regions(source: str, lines: list[str]) -> list[Region]:
    tree = ast.parse(source)
    regions: list[Region] = []
    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue

        region = Region(name=node.name)
        current_section: str | None = None
        for position, item in enumerate(node.body):
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                kind = FUNCTION
                has_doc = ast.get_docstring(item) is not None
            elif isinstance(item, (ast.Assign, ast.AnnAssign)):
                kind = CONSTANT
                following = (
                    node.body[position + 1] if position + 1 < len(node.body) else None
                )
                has_doc = python_docstring_below(item, following)
            else:
                continue

            decl = item.lineno - 1
            for decorator in getattr(item, "decorator_list", ()):
                decl = min(decl, decorator.lineno - 1)
            lower = node.body[position - 1].end_lineno if position > 0 else node.lineno
            block_start = comment_block_start(lines, decl, lower, ".py")
            section, _ = split_block(lines, block_start, decl, ".py")
            if not section:
                block_start, section = section_above(lines, block_start, lower)
            if section:
                current_section = section

            member = Member(
                name=python_member_name(item, decl),
                kind=kind,
                block_start=block_start,
                decl=decl,
                has_doc=has_doc,
                section=current_section,
            )
            region.members.append(member)

        if not region.members:
            continue
        region.start = region.members[0].block_start
        regions.append(region)
    return regions


# ==================== 公共逻辑 ====================


def build_region(
    name: str,
    decls: list[tuple[str, int]],
    lines: list[str],
    lower: int,
    suffix: str,
    initial_section: str | None = None,
) -> Region | None:
    """把逐条声明整理成区域，并解析分类与注释"""
    if not decls:
        return None

    members: list[Member] = []
    current_section: str | None = initial_section
    previous_decl = lower
    for kind, decl in decls:
        block_start = comment_block_start(lines, decl, previous_decl, suffix)
        section, has_doc = split_block(lines, block_start, decl, suffix)
        if not section:
            block_start, section = section_above(lines, block_start, previous_decl)
        if section:
            current_section = section
        members.append(
            Member(
                name=member_name(lines, decl),
                kind=kind,
                block_start=block_start,
                decl=decl,
                has_doc=has_doc,
                section=current_section,
            )
        )
        previous_decl = decl + 1

    return Region(name=name, members=members, start=members[0].block_start)


def member_name(lines: list[str], decl: int) -> str:
    """从声明行取出成员名，取不到时回退成行号描述"""
    raw = lines[decl]
    matched = re.search(r"(\w+)\s*[=(:]", raw)
    if matched:
        return matched.group(1)
    return f"第 {decl + 1} 行成员"


def first_misplaced_function(members: list[Member]) -> Member | None:
    """返回第一个排在普通常量之后的函数成员，顺序符合时返回 None"""
    seen_constant = False
    for member in members:
        if member.kind == CONSTANT:
            seen_constant = True
        elif seen_constant:
            return member
    return None


def collect_files(paths: list[str]) -> list[Path]:
    files: list[Path] = []
    for raw in paths:
        path = Path(raw)
        if path.is_dir():
            files.extend(
                sorted(item for item in path.iterdir() if item.suffix in SUFFIXES)
            )
        elif path.is_file():
            files.append(path)
        else:
            raise FileNotFoundError(raw)
    return files


def parse_regions(path: Path, source: str, lines: list[str]) -> list[Region]:
    """按扩展名分发到对应语言的解析器"""
    suffix = path.suffix
    if suffix == ".java":
        return java_regions(lines)
    if suffix == ".ts":
        return typescript_regions(lines)
    if suffix == ".go":
        return propagate_sections(go_regions(lines))
    return python_regions(source, lines)


def propagate_sections(regions: list[Region]) -> list[Region]:
    """Go 的 const / var 语句各自成块，分类注释按文件顺序向后延续"""
    current: str | None = None
    for region in regions:
        members: list[Member] = []
        for member in region.members:
            if member.section:
                current = member.section
            members.append(replace(member, section=current))
        region.members = members
    return regions


def process_file(path: Path) -> list[str]:
    """返回该文件的问题描述列表"""
    source = path.read_text(encoding="utf-8")
    lines = source.split("\n")
    regions = parse_regions(path, source, lines)

    problems: list[str] = []
    for region in regions:
        for member in region.members:
            location = f"{path}:{member.decl + 1}"
            if not member.has_doc:
                problems.append(
                    f"{location} {region.name}.{member.name} 缺少注释，"
                    f"{doc_style_hint(path.suffix)}"
                )
            if not member.section:
                problems.append(
                    f"{location} {region.name}.{member.name} 未归入分类，"
                    f"需在其上方补单行分类注释 {section_style_hint(path.suffix)}"
                )

        if path.suffix not in ORDER_CHECKED:
            continue
        if first_misplaced_function(region.members) is not None:
            problems.append(
                f"{path}:{region.start + 1} 常量类 {region.name} 的函数成员排在普通常量之后"
            )

    problems.extend(section_spacing_problems(path, lines))
    return problems


def section_spacing_problems(path: Path, lines: list[str]) -> list[str]:
    """分类注释下方必须空一行，与成员的注释分开"""
    problems: list[str] = []
    for index, raw in enumerate(lines):
        if not SECTION_PATTERN.match(raw):
            continue
        following = lines[index + 1] if index + 1 < len(lines) else ""
        if following.strip():
            problems.append(
                f"{path}:{index + 2} 分类注释下方需要空一行，与下方的成员注释分开"
            )
    return problems


def doc_style_hint(suffix: str) -> str:
    """返回各语言的成员注释写法提示"""
    if suffix == ".py":
        return "普通常量写在变量下方一行用三双引号包裹，方法写在函数体首行"
    if suffix == ".go":
        return "写在成员上方，以 // 开头"
    return "写在成员上方，用 /** 单行说明 */ 包裹"


def section_style_hint(suffix: str) -> str:
    """返回各语言的分类注释写法提示"""
    prefix = "#" if suffix == ".py" else "//"
    return f"{prefix} ===== 分类名 ====="


def main() -> int:
    parser = argparse.ArgumentParser(description="常量文件规范检查")
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
        except (SyntaxError, UnicodeDecodeError) as error:
            print(f"[ERROR] {path} 解析失败: {error}")
            failed = True
            continue

        for problem in problems:
            print(f"[ERROR] {problem}")
            failed = True

    if failed:
        print("[ERROR] 存在不符合常量文件约定的文件，注释与分类需人工补齐")
        return 1

    print("[INFO] 常量文件规范检查通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())

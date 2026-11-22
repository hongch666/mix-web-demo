#!/usr/bin/env python3
"""OpenAPI 错误码一致性检查

扫描四个服务源码里实际出现的 HTTP 状态码（常量引用与字面量），与静态 OpenAPI
产物中声明的 responses 状态码对比，报告「源码里出现、文档里没声明」的码。

用途是发现遗漏的接口级错误响应声明：全局注入的 400/401/500 不会出现在差异里，
差异项即需要人工确认是否补 @ApiResponse / responses 的业务码。

退出码：默认 0（只报告，不阻断生成）；加 --strict 时存在差异返回 1。
"""

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# 只关心错误码区间，200/302 等成功与重定向不计入差异
ERROR_MIN = 400
ERROR_MAX = 599

SERVICES = ("spring", "gozero", "nestjs", "fastapi")


def parse_constants(path: Path, pattern: str) -> dict[str, int]:
    """从常量文件解析 name -> code 映射"""
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    return {name: int(code) for name, code in re.findall(pattern, text)}


class ServiceProbe:
    """单个服务的源码扫描与产物解析"""

    def __init__(self):
        self.sources = self._source_files()
        self.constants = self._load_constants()
        self.const_prefix = self._const_prefix()
        self.literal_patterns = self._literal_patterns()

    def _source_files(self) -> list[Path]:
        raise NotImplementedError

    def _load_constants(self) -> dict[str, int]:
        raise NotImplementedError

    def _const_prefix(self) -> str:
        raise NotImplementedError

    def _literal_patterns(self) -> list[str]:
        raise NotImplementedError

    def doc_path(self) -> Path:
        raise NotImplementedError

    def source_codes(self) -> dict[int, list[str]]:
        """返回源码里出现的错误码 -> 命中位置列表"""
        found: dict[int, list[str]] = {}
        const_regex = re.compile(rf"{re.escape(self.const_prefix)}([A-Za-z_]+)")
        literal_regexes = [re.compile(pattern) for pattern in self.literal_patterns]

        for path in self.sources:
            try:
                text = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            for line_no, line in enumerate(text.splitlines(), start=1):
                for name in const_regex.findall(line):
                    code = self.constants.get(name)
                    if code is not None:
                        self._record(found, code, path, line_no)
                for regex in literal_regexes:
                    for match in regex.findall(line):
                        value = match if isinstance(match, str) else match[0]
                        self._record(found, int(value), path, line_no)
        return found

    @staticmethod
    def _record(found: dict[int, list[str]], code: int, path: Path, line_no: int) -> None:
        if ERROR_MIN <= code <= ERROR_MAX:
            found.setdefault(code, []).append(f"{path.relative_to(ROOT)}:{line_no}")

    def documented_codes(self) -> set[int]:
        """返回产物里所有 operation 声明过的状态码"""
        doc = self.doc_path()
        if not doc.exists():
            return set()
        data = json.loads(doc.read_text(encoding="utf-8"))
        codes: set[int] = set()
        for path_item in (data.get("paths") or {}).values():
            if not isinstance(path_item, dict):
                continue
            for operation in path_item.values():
                if not isinstance(operation, dict):
                    continue
                for code in (operation.get("responses") or {}):
                    try:
                        codes.add(int(code))
                    except (TypeError, ValueError):
                        continue
        return codes


class SpringProbe(ServiceProbe):
    """Spring WebFlux：HttpCode 常量 + @ApiResponse(responseCode) 字面量"""

    def _source_files(self) -> list[Path]:
        base = ROOT / "spring/src/main/java"
        return [p for p in base.rglob("*.java") if p.name != "HttpCode.java"]

    def _load_constants(self) -> dict[str, int]:
        return parse_constants(
            ROOT / "spring/src/main/java/com/hcsy/spring/common/constants/HttpCode.java",
            r"public\s+static\s+final\s+int\s+([A-Z_]+)\s*=\s*(\d{3})",
        )

    def _const_prefix(self) -> str:
        return "HttpCode."

    def _literal_patterns(self) -> list[str]:
        return [
            r'responseCode\s*=\s*"(\d{3})"',
            r"Result\.error\(\s*(\d{3})",
            r"BusinessException\(\s*(\d{3})",
        ]

    def doc_path(self) -> Path:
        return ROOT / "spring/docs/openapi.json"


class GoZeroProbe(ServiceProbe):
    """GoZero：constants.HttpXxx 常量 + utils.Error 字面量"""

    def _source_files(self) -> list[Path]:
        base = ROOT / "gozero/app"
        return [
            p
            for p in base.rglob("*.go")
            if p.name != "httpCode.go" and not p.name.endswith("_test.go")
        ]

    def _load_constants(self) -> dict[str, int]:
        return parse_constants(
            ROOT / "gozero/app/common/constants/httpCode.go",
            r"(Http[A-Za-z]+)\s*=\s*(\d{3})",
        )

    def _const_prefix(self) -> str:
        return "constants."

    def _literal_patterns(self) -> list[str]:
        return [r"utils\.Error\(\s*\w+\s*,\s*(\d{3})"]

    def doc_path(self) -> Path:
        return ROOT / "gozero/app/docs/openapi.json"


class NestjsProbe(ServiceProbe):
    """NestJS：HttpCode 常量 + @ApiResponse({ status }) 字面量"""

    def _source_files(self) -> list[Path]:
        base = ROOT / "nestjs/src"
        return [
            p
            for p in base.rglob("*.ts")
            if p.name != "httpCode.constants.ts" and not p.name.endswith(".spec.ts")
        ]

    def _load_constants(self) -> dict[str, int]:
        return parse_constants(
            ROOT / "nestjs/src/common/constants/httpCode.constants.ts",
            r"static\s+readonly\s+([A-Z_]+)\s*=\s*(\d{3})",
        )

    def _const_prefix(self) -> str:
        return "HttpCode."

    def _literal_patterns(self) -> list[str]:
        return [
            r"status:\s*(\d{3})",
            r"status_code\s*[:=]\s*(\d{3})",
            r"HttpException\([^,]+,\s*(\d{3})",
        ]

    def doc_path(self) -> Path:
        return ROOT / "nestjs/docs/openapi.json"


class FastapiProbe(ServiceProbe):
    """FastAPI：HttpCode 常量 + responses 键与 status_code 字面量"""

    def _source_files(self) -> list[Path]:
        base = ROOT / "fastapi/app"
        return [p for p in base.rglob("*.py") if p.name != "httpCode.py"]

    def _load_constants(self) -> dict[str, int]:
        return parse_constants(
            ROOT / "fastapi/app/core/constants/httpCode.py",
            r"^\s*([A-Z_]+)\s*:\s*int\s*=\s*(\d{3})",
        )

    def _const_prefix(self) -> str:
        return "HttpCode."

    def _literal_patterns(self) -> list[str]:
        return [
            r"status_code\s*=\s*(\d{3})",
            r"raise\s+BusinessException\(\s*(\d{3})",
            r"^\s*(\d{3}):\s*\{",
        ]

    def doc_path(self) -> Path:
        return ROOT / "fastapi/docs/openapi.json"


PROBES = {
    "spring": SpringProbe,
    "gozero": GoZeroProbe,
    "nestjs": NestjsProbe,
    "fastapi": FastapiProbe,
}


def format_codes(codes) -> str:
    return " ".join(str(code) for code in sorted(codes)) or "(无)"


def main() -> int:
    parser = argparse.ArgumentParser(description="检查 OpenAPI 错误码与源码的一致性")
    parser.add_argument("services", nargs="*", help="要检查的服务，缺省为全部")
    parser.add_argument(
        "--strict", action="store_true", help="存在差异时返回非零退出码"
    )
    args = parser.parse_args()

    targets = args.services or list(SERVICES)
    unknown = [name for name in targets if name not in PROBES]
    if unknown:
        print(f"未知服务: {', '.join(unknown)}", file=sys.stderr)
        return 2

    has_diff = False
    for name in targets:
        probe = PROBES[name]()
        source = probe.source_codes()
        documented = probe.documented_codes()
        if not probe.doc_path().exists():
            print(f"[{name}] 产物缺失: {probe.doc_path().relative_to(ROOT)}（先运行 ./mix swag {name}）")
            has_diff = True
            continue

        missing = sorted(set(source) - documented)
        print(f"=== {name} ===")
        print(f"  文档状态码: {format_codes(documented)}")
        print(f"  源码错误码: {format_codes(source)}")
        if not missing:
            print("  结果: 一致")
            continue

        has_diff = True
        print(f"  源码出现但文档未声明: {format_codes(missing)}")
        for code in missing:
            locations = source[code][:3]
            suffix = " ..." if len(source[code]) > 3 else ""
            print(f"    {code}: {', '.join(locations)}{suffix}")
        print("  处置: 确认是真实接口错误码后在代码声明处补 @ApiResponse / responses / .api 映射")

    if has_diff and args.strict:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

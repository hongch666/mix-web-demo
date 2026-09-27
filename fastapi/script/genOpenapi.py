"""生成 FastAPI 侧的 OpenAPI 静态产物（JSON 与 YAML 两份）

不启动 uvicorn、不执行 lifespan，仅导入应用工厂并调用 app.openapi()，
因此不依赖 MySQL、Redis、RabbitMQ 等任何中间件，也不需要 .env

用法：
    python script/genOpenapi.py [输出路径]

默认输出到 FastAPI 模块自身的 docs/openapi.json 与 docs/openapi.yaml
"""

import json
import sys
from pathlib import Path

import yaml

# 保证脚本在任意工作目录下都能导入 app 包
FASTAPI_ROOT = Path(__file__).resolve().parents[1]
if str(FASTAPI_ROOT) not in sys.path:
    sys.path.insert(0, str(FASTAPI_ROOT))

from app import create_app  # noqa: E402

DEFAULT_OUTPUT = FASTAPI_ROOT / "docs" / "openapi.json"


def write_json(path: Path, schema: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    # newline="\n" 必须有：write_text 默认按 os.linesep 转换，Windows 下会写成 CRLF
    path.write_text(
        json.dumps(schema, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def write_yaml(path: Path, schema: dict[str, object]) -> None:
    """与 GoZero 的 fix.py 使用同一组 PyYAML 参数，保证各服务 YAML 风格一致"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(
            schema,
            allow_unicode=True,
            default_flow_style=False,
            sort_keys=False,
        ),
        encoding="utf-8",
        newline="\n",
    )


def main() -> None:
    output: Path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_OUTPUT
    yaml_output: Path = output.with_suffix(".yaml")

    app = create_app()
    schema: dict[str, object] = app.openapi()

    write_json(output, schema)
    write_yaml(yaml_output, schema)

    paths: dict[str, object] = schema.get("paths", {}) or {}
    print(
        f"FastAPI OpenAPI 文档已生成: {output}、{yaml_output}"
        f"（接口路径 {len(paths)} 个）"
    )


if __name__ == "__main__":
    main()

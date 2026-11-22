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

# 401 统一错误响应的描述文案
UNAUTHORIZED_DESCRIPTION = "用户未登录或登录已失效"

# 统一错误响应的 schema 名
ERROR_SCHEMA_NAME = "ErrorResponse"

# 全局通用错误码与描述：
#   400  RequestValidationError 被 business_exception_handler 统一映射为 400
#   401  鉴权依赖未取到登录身份
#   500  全局异常兜底
COMMON_ERROR_RESPONSES = (
    ("400", "请求参数校验失败"),
    ("401", UNAUTHORIZED_DESCRIPTION),
    ("500", "服务器内部错误"),
)

# FastAPI 默认按自身约定为带参接口声明 422 校验错误，但项目把 RequestValidationError
# 统一映射成 400（见 exceptionHandlers），实际不会返回 422，产物里必须剔除以免文档失真
FASTAPI_DEFAULT_VALIDATION_STATUS = "422"

# 网关 block-internal 路由返回的 403 描述，与 apisix.yaml 的 response_example 对齐
GATEWAY_FORBIDDEN_DESCRIPTION = "内部接口禁止外部访问"

# 共享的网关黑名单 JSON（由 scripts/swag-init.sh 在生成前从 apisix.yaml 抽取）
GATEWAY_BLOCKLIST_JSON = FASTAPI_ROOT.parent / "scripts" / "generated" / "gateway-blocklist.json"


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


def is_error_status(code: object) -> bool:
    """判断响应状态码是否落在 400~599 的错误区间

    OpenAPI 的 responses 键既有数字也有 default 这类占位键，非数字一律视为非错误码
    """
    try:
        value = int(str(code))
    except (TypeError, ValueError):
        return False
    return 400 <= value <= 599


def load_gateway_blocklist() -> list[str]:
    """读取共享的网关黑名单 JSON，文件不存在时返回空列表"""
    if not GATEWAY_BLOCKLIST_JSON.is_file():
        return []
    try:
        data = json.loads(GATEWAY_BLOCKLIST_JSON.read_text(encoding="utf-8"))
        return list(data.get("uris", []))
    except (OSError, ValueError):
        return []


def is_gateway_blocked(path: str, blocklist: list[str]) -> bool:
    """OpenAPI path 是否命中网关黑名单：精确匹配或以 * 结尾的前缀匹配"""
    for uri in blocklist:
        if uri.endswith("*"):
            if path.startswith(uri[:-1]):
                return True
        elif path == uri:
            return True
    return False


def add_gateway_internal_responses(schema: dict[str, object]) -> None:
    """为网关 block-internal 拦截的接口补 403，只补描述，错误体由通用逻辑补齐"""
    blocklist = load_gateway_blocklist()
    if not blocklist:
        return
    for path, path_item in (schema.get("paths") or {}).items():
        if not isinstance(path_item, dict) or not is_gateway_blocked(path, blocklist):
            continue
        for method, operation in path_item.items():
            if method not in ("get", "post", "put", "delete", "patch", "head", "options"):
                continue
            if not isinstance(operation, dict):
                continue
            responses: dict[str, object] = operation.setdefault("responses", {})
            if "403" in responses and isinstance(responses["403"], dict):
                # 网关是外部第一道关，被拦截的接口统一用网关描述覆盖应用级 403
                responses["403"]["description"] = GATEWAY_FORBIDDEN_DESCRIPTION
            else:
                responses["403"] = {"description": GATEWAY_FORBIDDEN_DESCRIPTION}


def add_common_error_responses(schema: dict[str, object]) -> None:
    """为所有接口补全局通用错误响应（400、401、500）

    参数校验失败、未登录/令牌失效与未捕获异常由 business_exception_handler 统一转为
    error(code=..., msg=...)，这些响应对所有接口通用，这里统一注入，避免每个路由重复声明。
    同时剔除 FastAPI 自动声明的 422：项目把 RequestValidationError 映射为 400，实际不返回 422
    """
    components: dict[str, object] = schema.setdefault("components", {})  # type: ignore[assignment]
    schemas: dict[str, object] = components.setdefault("schemas", {})  # type: ignore[assignment]
    if ERROR_SCHEMA_NAME not in schemas:
        schemas[ERROR_SCHEMA_NAME] = {
            "type": "object",
            "description": "统一错误响应",
            "properties": {
                "code": {
                    "type": "integer",
                    "format": "int32",
                    "example": 400,
                    "description": "响应码，与 HTTP 状态码一致",
                },
                "msg": {"type": "string", "description": "响应消息"},
                "data": {"type": "null", "description": "返回数据"},
            },
            "required": ["code", "msg", "data"],
        }

    ref = f"#/components/schemas/{ERROR_SCHEMA_NAME}"
    for path_item in (schema.get("paths") or {}).values():
        if not isinstance(path_item, dict):
            continue
        for method, operation in path_item.items():
            if method not in (
                "get",
                "post",
                "put",
                "delete",
                "patch",
                "head",
                "options",
            ):
                continue
            if not isinstance(operation, dict):
                continue
            responses: dict[str, object] = operation.setdefault("responses", {})  # type: ignore[assignment]
            responses.pop(FASTAPI_DEFAULT_VALIDATION_STATUS, None)
            error_content = {"application/json": {"schema": {"$ref": ref}}}
            for code, description in COMMON_ERROR_RESPONSES:
                if code in responses:
                    continue
                responses[code] = {
                    "description": description,
                    "content": error_content,
                }
            # 路由 responses 里声明的业务错误码可能只给描述，
            # 统一错误体在这里补齐，保证每个错误响应都有可引用的结构
            for code, response in responses.items():
                if (
                    isinstance(response, dict)
                    and "content" not in response
                    and is_error_status(code)
                ):
                    response["content"] = error_content


def main() -> None:
    output: Path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_OUTPUT
    yaml_output: Path = output.with_suffix(".yaml")

    app = create_app()
    schema: dict[str, object] = app.openapi()
    add_gateway_internal_responses(schema)
    add_common_error_responses(schema)

    write_json(output, schema)
    write_yaml(yaml_output, schema)

    paths: dict[str, object] = schema.get("paths", {}) or {}
    print(
        f"FastAPI OpenAPI 文档已生成: {output}、{yaml_output}"
        f"（接口路径 {len(paths)} 个）"
    )


if __name__ == "__main__":
    main()

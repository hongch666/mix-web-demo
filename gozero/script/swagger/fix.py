"""
goctl 产物后处理：补中文标签、剔除易变字段与 WebSocket 路径，并由 JSON 派生 YAML

由 genSwagger.sh 在 swagger2openapi 转换为 OpenAPI 3 之后调用
"""

import copy
import json
import os
import re
import sys

try:
    import yaml
except ImportError:
    yaml = None

# WebSocket 路径：OpenAPI/Swagger 无法表达 WebSocket，Apifox 里它是独立资源类型，
# 导入只会多出一条无法发起 WS 握手的 GET 接口，因此从产物中剔除，由 Apifox 侧手工维护
WEBSOCKET_PATHS = ("/ws/chat",)

# goctl 写入的易变元信息：
#   x-date           生成时刻，同一份 .api 每次生成都不同
#   x-goctl-version  goctl 版本，升级工具后就会变
# 两者都会让提交的产物产生无意义 diff，因此从产物中剔除
VOLATILE_FIELDS = ("x-date", "x-goctl-version")

# 没有数据的响应统一声明为空数据类型：
# goctl 对 SyncESResp 这类空结构体只会生成裸 {"type": "object"}，
# 实空壳用 utils.Success 包装后 data 实际是 null，留成 object 会让 Apifox 展示一个空对象示例
# 声明与 NestJS 的 SwaggerNullData 保持一致
EMPTY_DATA_SCHEMA = {"type": "null", "description": "响应数据"}

# OpenAPI 3.1 里表示「允许为 null」的类型标记
NULL_TYPE = "null"

# SSE 帧在 application/json 视图下的 schema 标题
# Apifox 用 schema 的 title 作为「返回响应」里的节点名，FastAPI 侧由框架按 response_model
# 自动生成（形如 Response Stream Message Chat Stream Post），GoZero 这里显式给出帧类型名
SSE_FRAME_SCHEMA_TITLE = "ChatSSEMessage"

# 401 统一错误响应的描述文案
UNAUTHORIZED_DESCRIPTION = "用户未登录或登录已失效"

# 401 统一错误响应的 schema 名
UNAUTHORIZED_SCHEMA_NAME = "UnauthorizedResponse"

# 提升为具名响应模型时加的服务前缀
# Apifox 的 targetSchemaFolderId 是四个服务共用的同一个模型目录，而 GoZero 与 NestJS
# 存在同名路径（/sql-tools/query、/task/syncer），不加前缀会在同一目录里互相覆盖
SERVICE_MODEL_PREFIX = "Gozero"

# 只有带结构信息的内联 schema 才提升为具名模型，裸 object 与标量提升后只是噪音
STRUCTURAL_SCHEMA_KEYS = ("properties", "items", "allOf", "anyOf", "oneOf", "enum")

# SSE 帧必须保持内联：Apifox 依赖内联的帧 schema 渲染 text/event-stream 响应
NON_HOISTED_MEDIA_TYPES = ("text/event-stream",)

# 产物的规范版本：留 3.1 是为了表达 type: "null"（空数据响应，Apifox 靠它展示空值）
# 该写法只有 3.1 合法，3.0 的 type 只接受 array/boolean/integer/number/object/string
# 服务内嵌的 swagger-ui 资源为 5.x（支持 3.1）；4.x 只认 swagger 2.0 与 openapi 3.0.x，会直接白屏
# 这里统一固定，顺带消除 swagger2openapi 版本差异造成的产物抖动
OPENAPI_VERSION = "3.1.0"


def mark_schema_nullable(schema):
    """递归标记 schema 里可空的属性

    判定规则：
    1. 未列入 required 的属性（`.api` 里标了 json:",optional"）——字段可缺省，Apifox 允许缺省却把 null 判成非法
    2. 切片属性（type: array）——Go 的 nil slice 经 json.Marshal 就是 null，即使字段必填也会输出 null
    $ref 与 enum 无法在 3.1 里直接扩展，保持原样
    """
    if not isinstance(schema, dict):
        return

    properties = schema.get("properties")
    if isinstance(properties, dict):
        required = schema.get("required")
        required = required if isinstance(required, list) else []
        for name, prop in properties.items():
            if not isinstance(prop, dict):
                continue
            if name in required and prop.get("type") != "array":
                continue
            mark_property_nullable(prop)

    mark_schema_nullable(schema.get("items"))

    additional = schema.get("additionalProperties")
    if isinstance(additional, dict):
        mark_schema_nullable(additional)

    for key in ("allOf", "anyOf", "oneOf"):
        for branch in schema.get(key) or []:
            mark_schema_nullable(branch)


def mark_property_nullable(prop):
    """把单个属性的 type 补成 [X, "null"]，已是数组形式时追加 null"""
    if not isinstance(prop, dict) or "$ref" in prop or "enum" in prop:
        return
    kind = prop.get("type")
    if isinstance(kind, list):
        if NULL_TYPE not in kind:
            kind.append(NULL_TYPE)
        return
    if not isinstance(kind, str) or kind == NULL_TYPE:
        return
    prop["type"] = [kind, NULL_TYPE]


def mark_nullable_properties(swagger_data):
    """为可空字段补上 OpenAPI 3.1 的 null 类型

    3.1 用类型数组表达可空（如 ["string","null"]），nullable: true 是 3.0 的写法、
    在 3.1 下会被忽略。不补的表现是 Apifox「校验响应」把合法的 null 判成
    「$.data.xxx 不允许为 null」
    """
    components = swagger_data.get("components") or {}
    schemas = components.get("schemas")
    if isinstance(schemas, dict):
        for schema in schemas.values():
            mark_schema_nullable(schema)

    for methods in (swagger_data.get("paths") or {}).values():
        if not isinstance(methods, dict):
            continue
        for details in methods.values():
            if not isinstance(details, dict):
                continue
            request_content = (details.get("requestBody") or {}).get("content") or {}
            for media in request_content.values():
                if isinstance(media, dict):
                    mark_schema_nullable(media.get("schema"))
            for response in (details.get("responses") or {}).values():
                if not isinstance(response, dict):
                    continue
                for media in (response.get("content") or {}).values():
                    if isinstance(media, dict):
                        mark_schema_nullable(media.get("schema"))


def add_chinese_tags_to_dict(swagger_data):
    """
    为swagger数据字典添加中文标签定义和info信息，并修复 schemes/servers
    此函数可以用于处理JSON和YAML数据
    返回 (处理后的 swagger 数据, WebSocket 接口描述列表)
    """

    # 中文标签映射
    tag_mapping = {
        "chat": {
            "name": "聊天模块",
            "description": "聊天功能相关API，包括消息发送、历史查询、队列管理等",
        },
        "search": {
            "name": "搜索模块",
            "description": "文章搜索功能相关API，支持多条件搜索、历史记录等",
        },
        "test": {
            "name": "测试模块",
            "description": "服务测试相关API，用于验证各个微服务是否正常运行",
        },
        "task": {
            "name": "定时任务模块",
            "description": "定时任务相关API，包括手动触发同步ES等任务操作",
        },
        "sqlTools": {
            "name": "SQL工具模块",
            "description": "SQL 执行工具相关API，包括表结构查询与只读参数化SQL查询",
        },
    }

    # 固定规范版本，保证两个生成脚本产物一致
    swagger_data["openapi"] = OPENAPI_VERSION

    # 覆盖 info 标题和描述，面向 Swagger 读者；.api 的 title/desc 只给开发者看，生成时会被这里替换
    if "info" not in swagger_data:
        swagger_data["info"] = {}
    swagger_data["info"]["title"] = "GoZero部分的Swagger文档"
    swagger_data["info"]["description"] = "这是项目的GoZero部分的Swagger文档"
    swagger_data["info"]["version"] = "1.0.0"
    swagger_data["info"]["x-author"] = "hongch666"

    # 添加tags定义
    swagger_data["tags"] = []

    # 添加中文标签定义
    for tag_key, tag_info in tag_mapping.items():
        swagger_data["tags"].append(
            {
                "name": tag_info["name"],
                "description": tag_info["description"],
                "x-english-name": tag_key,  # 保存原始英文名称作为扩展信息
            }
        )

    # 移除 swagger2openapi 自动注入的全局 servers 字段
    # 根因：Swagger 2.0 文档里没有 host，转换工具默认生成 https:// 的 server
    # 删除后 Swagger UI 会回退使用当前页面的 host + protocol，避免协议错误
    if "servers" in swagger_data:
        del swagger_data["servers"]

    # 更新所有路径中的tags为中文名称，并移除swagger2openapi注入的per-operation schemes/servers
    if "paths" in swagger_data:
        for methods in swagger_data["paths"].values():
            # 移除 path 级别可能存在的 servers（OpenAPI 3.0 允许 path 级 server）
            if isinstance(methods, dict) and "servers" in methods:
                del methods["servers"]

            for details in methods.values():
                if isinstance(details, dict):
                    # 将英文标签转换为对应的中文标签
                    if "tags" in details:
                        tags = details["tags"]
                        new_tags = []
                        for tag in tags:
                            if tag in tag_mapping:
                                new_tags.append(tag_mapping[tag]["name"])
                            else:
                                new_tags.append(tag)
                        details["tags"] = new_tags

                    # 移除 per-operation schemes（swagger2openapi 会注入 https，导致前端用错协议）
                    if "schemes" in details:
                        del details["schemes"]

                    # 移除 per-operation servers（swagger2openapi 会在每个 operation 下注入 https 的 servers）
                    if "servers" in details:
                        del details["servers"]

    # 剔除 goctl 写入的易变字段，避免每次生成都产生无意义 diff
    drop_volatile_fields(swagger_data)

    # 修正 SSE 长连接接口的响应声明
    fix_streaming_endpoints(swagger_data)

    # goctl 只根据 returns 生成 data 的 schema，实际 handler 模板会通过
    # utils.Success/Error 统一包装为 {code, msg, data}，这里补齐文档外壳
    wrap_unified_responses(swagger_data)

    # 401 未登录响应对所有接口通用，统一注入（必须在 wrap_unified_responses 之后，
    # 否则会被当成业务数据再包一层 code/msg/data 外壳）
    add_common_unauthorized_response(swagger_data)

    # 先摘出 WebSocket 接口的描述与标签，随后该路径会被剔除，改由 apifox-sync.sh
    # 通过 Apifox CLI 的 websocket 命令单独同步
    websocket_endpoints = collect_websocket_endpoints(swagger_data)

    # 剔除 WebSocket 路径（OpenAPI 无法表达这类资源，留在产物里只会多出无法握手的一条 GET）
    drop_websocket_paths(swagger_data)

    # 把内联请求体与响应结构提升为 components.schemas 具名模型，供 Apifox 复用与变更比对
    # 必须排在 wrap_unified_responses 之后：提升的是补好统一外壳的完整响应；
    # 必须排在 drop_websocket_paths 之后：否则被剔除的 WS 响应会留下无人引用的孤儿模型
    hoist_inline_models(swagger_data)

    # 最后补可空声明：模型与内联结构都已定型，此时补不会漏掉任何一层
    mark_nullable_properties(swagger_data)

    return swagger_data, websocket_endpoints


def wrap_unified_responses(swagger_data):
    """为 JSON 响应补齐 GoZero handler 模板实际输出的统一响应外壳。

    SSE 接口的 200 响应同时声明 text/event-stream 与 application/json
    （见 fix_streaming_endpoints），凡是内容类型里含 text/event-stream 的响应整体跳过，
    否则帧 schema 会被当成业务数据包进 code/msg/data 外壳。
    函数可重复执行：已经包含 code/msg/data 的 schema 不会再次嵌套
    """
    paths = swagger_data.get("paths")
    if not isinstance(paths, dict):
        return

    for path_item in paths.values():
        if not isinstance(path_item, dict):
            continue
        for operation in path_item.values():
            if not isinstance(operation, dict):
                continue
            responses = operation.get("responses")
            if not isinstance(responses, dict):
                continue
            for response in responses.values():
                if not isinstance(response, dict):
                    continue
                content = response.get("content")
                if not isinstance(content, dict):
                    continue
                # 事件流响应不属于统一 JSON 响应，该响应下的所有媒体类型都不改写
                if "text/event-stream" in content:
                    continue
                json_media = content.get("application/json")
                if not isinstance(json_media, dict):
                    continue
                schema = json_media.get("schema")
                if not isinstance(schema, dict):
                    schema = {}
                properties = schema.get("properties")
                if isinstance(properties, dict) and {
                    "code",
                    "msg",
                    "data",
                }.issubset(properties):
                    continue
                # Response models in .api may retain a Data field for frontend compatibility.
                # Success unwraps that field at runtime, so document its value directly.
                payload_schema = schema
                if isinstance(properties, dict) and "data" in properties:
                    payload_schema = properties["data"]
                # 无字段的响应体（SyncESResp、SSE 的 400 兜底体等）只有裸 object，实际 data 为 null
                if not isinstance(payload_schema, dict) or is_empty_object_schema(
                    payload_schema
                ):
                    payload_schema = dict(EMPTY_DATA_SCHEMA)

                json_media["schema"] = {
                    "type": "object",
                    "description": "GoZero 统一响应",
                    "properties": {
                        "code": {
                            "type": "integer",
                            "format": "int32",
                            "description": "响应码，与 HTTP 状态码一致",
                        },
                        "msg": {
                            "type": "string",
                            "description": "响应消息",
                        },
                        "data": payload_schema,
                    },
                    "required": ["code", "msg", "data"],
                }


def add_common_unauthorized_response(swagger_data):
    """为所有接口补统一的 401 未登录响应

    未登录或令牌失效由 utils.Error 统一输出 {code, msg, data}，
    该响应对所有接口通用，这里统一注入，避免每个 handler 重复声明。
    必须排在 wrap_unified_responses 之后：$ref 引用没有内联 properties，
    先注入会被误判成业务数据再包一层外壳
    """
    components = swagger_data.setdefault("components", {})
    if not isinstance(components, dict):
        return
    schemas = components.setdefault("schemas", {})
    if not isinstance(schemas, dict):
        return
    if UNAUTHORIZED_SCHEMA_NAME not in schemas:
        schemas[UNAUTHORIZED_SCHEMA_NAME] = {
            "type": "object",
            "description": "统一错误响应",
            "properties": {
                "code": {
                    "type": "integer",
                    "format": "int32",
                    "example": 401,
                    "description": "响应码，与 HTTP 状态码一致",
                },
                "msg": {"type": "string", "description": "响应消息"},
                "data": {"type": "null", "description": "响应数据"},
            },
            "required": ["code", "msg", "data"],
        }

    ref = f"#/components/schemas/{UNAUTHORIZED_SCHEMA_NAME}"
    paths = swagger_data.get("paths")
    if not isinstance(paths, dict):
        return
    for path_item in paths.values():
        if not isinstance(path_item, dict):
            continue
        for operation in path_item.values():
            if not isinstance(operation, dict):
                continue
            responses = operation.get("responses")
            if not isinstance(responses, dict):
                responses = {}
                operation["responses"] = responses
            if "401" in responses:
                continue
            responses["401"] = {
                "description": UNAUTHORIZED_DESCRIPTION,
                "content": {"application/json": {"schema": {"$ref": ref}}},
            }


def to_pascal_name(raw):
    """把路径片段或方法名转成 PascalCase 标识符片段"""
    parts = [part for part in re.split(r"[^0-9A-Za-z]+", str(raw)) if part]
    return "".join(part[:1].upper() + part[1:] for part in parts)


def build_model_name(path, method, suffix, status=None):
    """按「服务前缀 + 路径 + 方法 + 状态码」生成模型名

    用路径而不是 operationId 命名：路径是对外契约，Apifox 也按 method+path 识别接口，
    重命名 handler 不会牵动模型名。路径参数保留为 ByXxx 片段，避免 /articles 与
    /articles/{id} 生成同一个名字
    """
    segments = []
    for segment in str(path).split("/"):
        if not segment:
            continue
        if segment.startswith("{") and segment.endswith("}"):
            segments.append("By" + to_pascal_name(segment[1:-1]))
        elif segment.startswith(":"):
            segments.append("By" + to_pascal_name(segment[1:]))
        else:
            segments.append(to_pascal_name(segment))

    name = SERVICE_MODEL_PREFIX + "".join(segments) + to_pascal_name(method)
    if status is not None and str(status) != "200":
        name += to_pascal_name(status)
    return name + suffix


def reserve_model_name(schemas, path, method, suffix, schema, status=None):
    """为内联结构分配模型名：同名且内容一致时直接复用，内容不同则追加序号"""
    base = build_model_name(path, method, suffix, status)
    name = base
    index = 2
    while name in schemas and schemas[name] != schema:
        name = f"{base}_{index}"
        index += 1
    return name


def hoist_media_schema(schemas, path, method, suffix, content, status=None):
    """把一组 media type 下的内联 schema 提升为具名模型，原位置改为 $ref 引用"""
    for media_type, media in content.items():
        if media_type in NON_HOISTED_MEDIA_TYPES:
            continue
        if not isinstance(media, dict):
            continue
        schema = media.get("schema")
        if not isinstance(schema, dict) or "$ref" in schema:
            continue
        if not any(key in schema for key in STRUCTURAL_SCHEMA_KEYS):
            continue
        name = reserve_model_name(schemas, path, method, suffix, schema, status)
        schemas[name] = schema
        media["schema"] = {"$ref": f"#/components/schemas/{name}"}


def hoist_inline_models(swagger_data):
    """把各接口的内联请求体与响应结构提升为 components.schemas 具名模型

    goctl 按 .api 类型生成的是内联 schema，同一份结构在每个接口各存一份，Apifox 里既
    无法复用，也无法按模型维度比对变更。这里统一提升为具名模型：
    - 名称由「服务前缀 + 路径 + 方法 + 状态码」推导，服务前缀避免与 NestJS 同名路径互相覆盖
    - 事件流响应整体保持内联：Apifox 靠内联帧 schema 的 title 渲染流式响应
    - multipart 请求体保持内联：文件字段的 binary 表达交给 Apifox 按原生方式处理
    - 已是 $ref 的位置跳过，函数可重复执行
    """
    paths = swagger_data.get("paths")
    if not isinstance(paths, dict):
        return
    components = swagger_data.setdefault("components", {})
    if not isinstance(components, dict):
        return
    schemas = components.setdefault("schemas", {})
    if not isinstance(schemas, dict):
        return

    for path, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue
        for method, operation in path_item.items():
            if not isinstance(operation, dict):
                continue

            request_body = operation.get("requestBody")
            if isinstance(request_body, dict):
                request_content = request_body.get("content")
                if isinstance(request_content, dict) and "multipart/form-data" not in (
                    request_content
                ):
                    hoist_media_schema(
                        schemas, path, method, "Request", request_content
                    )

            responses = operation.get("responses")
            if not isinstance(responses, dict):
                continue
            for status, response in responses.items():
                if not isinstance(response, dict):
                    continue
                content = response.get("content")
                if not isinstance(content, dict):
                    continue
                # 事件流响应整体保持内联，换成 $ref 会丢掉帧节点名
                if "text/event-stream" in content:
                    continue
                hoist_media_schema(
                    schemas, path, method, "Response", content, status
                )


def is_empty_object_schema(schema):
    """判断是否为没有任何结构信息的裸 object

    只有 type 为 object，且没有 properties/additionalProperties/items/组合或引用时才成立，
    避免把 SqlToolsQueryResp 这类真正的 map 或结构体误判成空数据
    """
    if not isinstance(schema, dict) or schema.get("type") != "object":
        return False
    for key in (
        "properties",
        "additionalProperties",
        "items",
        "allOf",
        "anyOf",
        "oneOf",
        "$ref",
    ):
        if key in schema:
            return False
    return True


def drop_volatile_fields(swagger_data):
    """剔除每次都变化的生成元信息

    需要调整时改上面的 VOLATILE_FIELDS 常量
    """
    for field in VOLATILE_FIELDS:
        if swagger_data.pop(field, None) is not None:
            print(f"已从产物中剔除易变字段: {field}")


def fix_streaming_endpoints(swagger_data):
    """修正 SSE 长连接接口的响应声明

    /sse/chat 成功响应是 text/event-stream 持续数据帧，不是单次 JSON 响应
    参数非法时返回统一 JSON 错误体，goctl 未生成该响应，此处补齐

    帧 schema 同时挂到 application/json 下：Apifox 不会渲染只声明 text/event-stream
    的响应（「返回响应」里只显示 SSE 封装结构、无 schema），FastAPI 侧的流式聊天
    也是靠同一份帧 schema 的 JSON 视图才画出帧字段，这里与其保持一致

    WebSocket 路径不在此处理：它随后会被 drop_websocket_paths 整体剔除，
    若将来要改回保留，记得同时恢复 101 响应声明
    """
    paths = swagger_data.get("paths")
    if not isinstance(paths, dict):
        return

    sse_operation = paths.get("/sse/chat") or {}
    sse_get = sse_operation.get("get") if isinstance(sse_operation, dict) else None
    if isinstance(sse_get, dict):
        responses = sse_get.setdefault("responses", {})
        original_200 = responses.pop("200", None) or {}
        # goctl 已按 returns 类型生成 inline schema，这里直接复用，只把媒体类型换成事件流
        # 该文档的 schema 全部为 inline（components 下无 schemas），不能改成 $ref
        event_schema = None
        for media_obj in (original_200.get("content") or {}).values():
            if isinstance(media_obj, dict) and "schema" in media_obj:
                event_schema = media_obj["schema"]
                break
        if event_schema:
            # 深拷贝后再加 title，避免与 text/event-stream 下的同一份结构互相影响
            json_schema = copy.deepcopy(event_schema)
            json_schema["title"] = SSE_FRAME_SCHEMA_TITLE
            content = {
                "application/json": {"schema": json_schema},
                "text/event-stream": {"schema": event_schema},
            }
        else:
            content = {}
        responses["200"] = {
            "description": "连接建立成功，随后持续推送数据帧，每帧对应 ChatSSEMessage",
            "content": content,
        }

    if isinstance(sse_get, dict):
        sse_get.setdefault("responses", {}).setdefault(
            "400",
            {
                "description": "参数非法（如 user_id 非正整数）时返回统一 JSON 错误体",
                "content": {"application/json": {"schema": {"type": "object"}}},
            },
        )


def collect_websocket_endpoints(swagger_data):
    """摘出 WebSocket 接口中代码侧可确定归属的字段

    OpenAPI 无法表达 WebSocket，这些路径随后会被 drop_websocket_paths 剔除，
    所以先在这里取出来，由 apifox-sync.sh 通过 Apifox CLI 的 websocket 命令单独同步。
    只收 path、description、tags 三项：接口名称、参数、公共参数与目录归属由 Apifox
    侧手工维护（例如浏览器 WebSocket 无法自定义请求头，token 是以 query 参数手工补的），
    自动同步不能覆盖它们
    """
    paths = swagger_data.get("paths")
    if not isinstance(paths, dict):
        return []

    endpoints = []
    for path in WEBSOCKET_PATHS:
        path_item = paths.get(path)
        if not isinstance(path_item, dict):
            continue
        # goctl 把 WebSocket 路由生成为普通 get，取第一个可用的 operation
        for operation in path_item.values():
            if not isinstance(operation, dict):
                continue
            endpoint = {"path": path}
            description = operation.get("description") or operation.get("summary")
            if description:
                endpoint["description"] = description
            tags = operation.get("tags")
            if isinstance(tags, list) and tags:
                endpoint["tags"] = tags
            endpoints.append(endpoint)
            break

    return endpoints


def write_websocket_spec(swagger_file, endpoints):
    """把 WebSocket 接口描述写成独立产物

    与 openapi.json 同级，由 apifox-sync.sh 读取。没有 WebSocket 接口时也照常输出空数组，
    让同步脚本能区分「本次没有需要同步的接口」与「产物缺失」
    """
    websocket_file = os.path.join(
        os.path.dirname(os.path.abspath(swagger_file)), "websocket.json"
    )
    data = {
        "comment": "由 fix.py 从 goctl 产物提取，只含需要由代码同步到 Apifox 的字段",
        "websockets": endpoints,
    }

    try:
        with open(websocket_file, "w", encoding="utf-8", newline="\n") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")
    except Exception as e:
        print(f"错误: 写入 WebSocket 描述失败 - {e}")
        return False

    print(f"已生成 WebSocket 接口描述: {websocket_file}")
    return True


def drop_websocket_paths(swagger_data):
    """从产物中剔除 WebSocket 路径

    Apifox 的 WebSocket 接口是独立于 HTTP 的资源类型，OpenAPI/Swagger 无法表达，
    也没有对应的 x-apifox-* 扩展；导入时只会按 URL + method 建出一条 GET 接口，
    与 Apifox 里的 WebSocket 接口重复且无法发起 WS 握手，因此从可导入产物中剔除。
    剔除前由 collect_websocket_endpoints 摘出描述与标签，改走 Apifox CLI 单独同步
    需要调整时改上面的 WEBSOCKET_PATHS 常量
    """
    paths = swagger_data.get("paths")
    if not isinstance(paths, dict):
        return

    for path in WEBSOCKET_PATHS:
        if paths.pop(path, None) is not None:
            print(f"已从产物中剔除 WebSocket 路径: {path}")


def add_chinese_tags_json(swagger_file):
    """处理JSON文件"""
    if not os.path.exists(swagger_file):
        print(f"错误: 文件 {swagger_file} 不存在")
        return False

    try:
        with open(swagger_file, "r", encoding="utf-8") as f:
            swagger_data = json.load(f)

        swagger_data, websocket_endpoints = add_chinese_tags_to_dict(swagger_data)

        # 写回文件；newline="\n" 必须显式指定，否则 Windows 下会写成 CRLF
        with open(swagger_file, "w", encoding="utf-8", newline="\n") as f:
            json.dump(swagger_data, f, ensure_ascii=False, indent=2)

        print(f"已为 {swagger_file} 添加中文标签、信息描述和版本")

        # WebSocket 接口单独产出，OpenAPI 表达不了这类资源
        return write_websocket_spec(swagger_file, websocket_endpoints)

    except json.JSONDecodeError as e:
        print(f"错误: JSON解析失败 - {e}")
        return False
    except Exception as e:
        print(f"错误: {e}")
        return False


def write_yaml(swagger_file, swagger_data):
    """把处理好的数据写成 YAML 产物

    不再读取 goctl 生成的 YAML：那份是 Swagger 2.0，而 JSON 已被 swagger2openapi
    转成 OpenAPI 3，两边格式会分叉。这里直接由处理后的 JSON 派生 YAML，
    保证两份产物内容完全等价
    """
    if yaml is None:
        print("错误: PyYAML库未安装，无法生成 YAML 产物")
        print("请运行: pip install PyYAML")
        return False

    try:
        with open(swagger_file, "w", encoding="utf-8", newline="\n") as f:
            yaml.dump(
                swagger_data,
                f,
                allow_unicode=True,
                default_flow_style=False,
                sort_keys=False,
            )

        print(f"已由 JSON 派生 YAML 产物: {swagger_file}")
        return True

    except Exception as e:
        print(f"错误: 写入YAML失败 - {e}")
        return False


if __name__ == "__main__":
    json_file = sys.argv[1] if len(sys.argv) > 1 else "docs/openapi.json"
    yaml_file = sys.argv[2] if len(sys.argv) > 2 else "docs/openapi.yaml"

    if not add_chinese_tags_json(json_file):
        sys.exit(1)

    # 由已固定的 JSON 派生 YAML，避免两份产物在内容与格式上分叉
    with open(json_file, encoding="utf-8") as f:
        fixed_data = json.load(f)
    if not write_yaml(yaml_file, fixed_data):
        sys.exit(1)

    sys.exit(0)

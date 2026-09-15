#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为生成的swagger.json和swagger.yaml添加中文标签名和描述
"""

import json
import os
import sys

try:
    import yaml
except ImportError:
    yaml = None


def add_chinese_tags_to_dict(swagger_data):
    """
    为swagger数据字典添加中文标签定义和info信息，并修复 schemes/servers
    此函数可以用于处理JSON和YAML数据
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

    # 添加info的描述字段和版本
    if "info" not in swagger_data:
        swagger_data["info"] = {}
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
        for path, methods in swagger_data["paths"].items():
            # 移除 path 级别可能存在的 servers（OpenAPI 3.0 允许 path 级 server）
            if isinstance(methods, dict) and "servers" in methods:
                del methods["servers"]

            for method, details in methods.items():
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

    # 修正长连接接口（SSE / WebSocket）的响应声明
    fix_streaming_endpoints(swagger_data)

    return swagger_data


def fix_streaming_endpoints(swagger_data):
    """修正长连接接口的响应声明

    /sse/chat 成功响应是 text/event-stream 持续数据帧，不是单次 JSON 响应
    /ws/chat 成功响应是 101 协议升级，之后通过 WebSocket 文本帧双向通信
    两者参数非法时返回统一 JSON 错误体，goctl 未生成该响应，此处补齐
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
        responses["200"] = {
            "description": "连接建立成功，随后持续推送数据帧，每帧对应 ChatSSEMessage",
            "content": (
                {"text/event-stream": {"schema": event_schema}} if event_schema else {}
            ),
        }

    ws_operation = paths.get("/ws/chat") or {}
    ws_get = ws_operation.get("get") if isinstance(ws_operation, dict) else None
    if isinstance(ws_get, dict):
        responses = ws_get.setdefault("responses", {})
        # 101 是协议升级响应，本身不带响应体，因此只写描述
        responses.pop("200", None)
        responses["101"] = {
            "description": "协议升级成功（Switching Protocols），之后通过 WebSocket 文本帧双向通信，帧结构对应 ChatWsMessage",
        }

    for endpoint in ("/sse/chat", "/ws/chat"):
        operation = paths.get(endpoint) or {}
        get_operation = operation.get("get") if isinstance(operation, dict) else None
        if isinstance(get_operation, dict):
            responses = get_operation.setdefault("responses", {})
            responses.setdefault(
                "400",
                {
                    "description": "参数非法（如 user_id 非正整数）时返回统一 JSON 错误体",
                    "content": {"application/json": {"schema": {"type": "object"}}},
                },
            )


def add_chinese_tags_json(swagger_file):
    """处理JSON文件"""
    if not os.path.exists(swagger_file):
        print(f"错误: 文件 {swagger_file} 不存在")
        return False

    try:
        with open(swagger_file, "r", encoding="utf-8") as f:
            swagger_data = json.load(f)

        swagger_data = add_chinese_tags_to_dict(swagger_data)

        # 写回文件
        with open(swagger_file, "w", encoding="utf-8") as f:
            json.dump(swagger_data, f, ensure_ascii=False, indent=2)

        print(f"已为 {swagger_file} 添加中文标签、信息描述和版本")
        return True

    except json.JSONDecodeError as e:
        print(f"错误: JSON解析失败 - {e}")
        return False
    except Exception as e:
        print(f"错误: {e}")
        return False


def add_chinese_tags_yaml(swagger_file):
    """处理YAML文件"""
    if not os.path.exists(swagger_file):
        print(f"错误: 文件 {swagger_file} 不存在")
        return False

    if yaml is None:
        print("警告: PyYAML库未安装，跳过YAML文件处理")
        print("请运行: pip install PyYAML")
        return False

    try:
        with open(swagger_file, "r", encoding="utf-8") as f:
            swagger_data = yaml.safe_load(f)

        if swagger_data is None:
            print(f"错误: YAML文件无法解析 - {swagger_file}")
            return False

        swagger_data = add_chinese_tags_to_dict(swagger_data)

        # 写回文件
        with open(swagger_file, "w", encoding="utf-8") as f:
            yaml.dump(
                swagger_data,
                f,
                allow_unicode=True,
                default_flow_style=False,
                sort_keys=False,
            )

        print(f"已为 {swagger_file} 添加中文标签、信息描述和版本")
        return True

    except yaml.YAMLError as e:
        print(f"错误: YAML解析失败 - {e}")
        return False
    except Exception as e:
        print(f"错误: {e}")
        return False


if __name__ == "__main__":
    json_file = sys.argv[1] if len(sys.argv) > 1 else "docs/main.json"
    yaml_file = sys.argv[2] if len(sys.argv) > 2 else "docs/main.yaml"

    json_success = add_chinese_tags_json(json_file)
    yaml_success = add_chinese_tags_yaml(yaml_file)

    if json_success and yaml_success:
        sys.exit(0)
    elif json_success:
        print("JSON文件处理成功，YAML文件处理失败（可忽略，不影响主流程）")
        sys.exit(0)  # YAML 失败不视为致命错误
    else:
        sys.exit(1)

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

    return swagger_data


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
        print("JSON文件处理成功，YAML文件处理失败")
        sys.exit(1)
    else:
        sys.exit(1)

from typing import Any


class SwaggerConfig:
    """
    Swagger/OpenAPI 配置类
    """

    # ===== 文档基础信息 =====

    SWAGGER_TITLE: str = "FastAPI部分的Swagger文档"
    """文档标题"""
    SWAGGER_DESCRIPTION: str = (
        "**服务职责**：AI 聊天（含 SSE 流式）、LangChain RAG 与 Agent 工具调用、知识图谱查询、"
        "向量搜索增强、文章与用户行为数据分析（ClickHouse）、Excel 导出与定时任务；"
        "对外统一经 APISIX 网关（8080）访问。\n"
        "\n"
        '**统一响应**：除流式接口外，所有接口返回 `{"code": 200, "msg": "...", "data": ...}`，'
        "code 与 HTTP 状态码一致；无返回数据的接口 data 为 null。\n"
        "\n"
        "**流式接口**：/chat/stream 的 200 响应同时声明 text/event-stream 与 JSON 视图，"
        "文档中可展开查看帧结构。\n"
        "\n"
        "**字段命名**：请求与响应字段统一 snake_case。\n"
        "\n"
        "**认证方式**：需登录的接口由网关透传的用户身份校验，未登录或令牌失效返回 401；"
        "服务间调用使用 X-Internal-Token 请求头。\n"
        "\n"
        "**文档来源**：由 FastAPI 应用内 OpenAPI 描述离线导出（OpenAPI 3.1），模型取自 Pydantic。"
    )
    """文档描述"""
    SWAGGER_VERSION: str = "1.0.0"
    """接口版本号"""
    OPENAPI_VERSION: str = "3.1.0"
    """产物的 OpenAPI 规范版本，3.1 才能表达空值响应"""
    STREAM_CHAT_RESPONSES: dict[int | str, dict[str, Any]] = {
        200: {
            "description": "SSE 流式响应：native 返回 ChatResponse，openai 返回 OpenAIStreamChunk",
            "content": {
                "text/event-stream": {
                    "schema": {
                        "oneOf": [
                            {"$ref": "#/components/schemas/ChatResponse"},
                            {"$ref": "#/components/schemas/OpenAIStreamChunk"},
                        ]
                    }
                }
            },
        }
    }
    """流式聊天接口的响应声明，200 同时挂 SSE 与两种帧结构"""
    OPENAPI_TAGS = [
        {
            "name": "AI历史模块",
            "description": "AI历史相关API，包括创建AI历史记录、获取所有AI历史记录、删除用户所有AI历史记录等",
        },
        {
            "name": "用户个人数据分析模块",
            "description": "用户个人数据分析相关API，包括获取新增粉丝数统计、获取文章浏览分布、获取关注作者统计、获取本月评论/点赞/收藏趋势等",
        },
        {
            "name": "文章分析模块",
            "description": "文章分析相关API，包括获取前10篇文章、生成词云图、获取文章统计信息等",
        },
        {
            "name": "API日志分析模块",
            "description": "API日志分析相关API，包括获取所有接口的平均响应速度、获取接口调用次数等",
        },
        {
            "name": "测试模块",
            "description": "服务测试相关API，包括测试FastAPI服务、测试Spring服务、测试GoZero服务、测试NestJS服务等",
        },
        {
            "name": "AI聊天模块",
            "description": "AI聊天相关API，包括普通聊天和流式聊天",
        },
        {
            "name": "生成模块",
            "description": "生成相关API，包括生成tags、为文章创建AI评论、为文章创建基于权威参考文本的AI评论等",
        },
        {
            "name": "知识图谱模块",
            "description": "知识图谱相关API，包括图谱搜索、图谱增强等功能",
        },
        {
            "name": "向量搜索模块",
            "description": "向量搜索相关API，包括根据 ES 候选文章进行语义分、语义原因和匹配片段增强",
        },
        {
            "name": "算法模块",
            "description": "算法相关API，包括提供ES复合打分和融合排序所需的全量权重参数",
        },
        {
            "name": "定时任务模块",
            "description": "定时任务相关API，包括手动触发同步ES等任务操作",
        },
    ]
    """接口分组标签，与路由上的 tags 对应"""

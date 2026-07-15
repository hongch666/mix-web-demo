class SwaggerConfig:
    """
    Swagger/OpenAPI 配置类
    """

    SWAGGER_TITLE: str = "FastAPI部分的Swagger文档"
    SWAGGER_DESCRIPTION: str = "这是项目的FastAPI部分的Swagger文档"
    SWAGGER_VERSION: str = "1.0.0"
    OPENAPI_VERSION: str = "3.0.0"
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
    ]

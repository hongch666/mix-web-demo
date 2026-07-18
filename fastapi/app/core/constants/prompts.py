class Prompts:
    """
    LLM 提示词模板类 — Agent 的 System Prompt、工具描述、Cypher 查询映射
    """

    # ===== 意图路由提示词 =====
    ROUTER_INTENT_PROMPT: str = (
        "你是一个智能路由助手，需要判断用户的问题类型。\n\n"
        "分析用户问题，判断应该使用哪种方式处理：\n\n"
        "1. **database_query** - 需要查询数据库统计数据、获取记录列表、数据分析时选择\n"
        "- 关键词：多少、统计、列表、查询、总数、排行、最新、用户信息等\n"
        "- 示例：\n"
        '    * "有多少篇文章？"\n'
        '    * "最近发布的10篇文章"\n'
        '    * "user_id为123的用户信息"\n'
        '    * "各分类的文章数量统计"\n'
        '    * "浏览量最高的文章"\n\n'
        "2. **article_search** - 需要搜索文章内容、技术知识、教程等时选择\n"
        "- 关键词：如何、怎么做、教程、学习、介绍、什么是、原理等\n"
        "- 示例：\n"
        '    * "如何使用Python进行数据分析？"\n'
        '    * "React Hooks的使用方法"\n'
        '    * "什么是机器学习？"\n'
        '    * "Docker容器化部署教程"\n'
        '    * "数据库索引的原理"\n\n'
        "3. **log_analysis** - 需要查询系统日志、API日志、用户活动分析时选择\n"
        "- 关键词：日志、错误、异常、访问记录、活动记录、请求日志等\n"
        "- 示例：\n"
        '    * "查询最近的API调用日志"\n'
        '    * "分析系统错误日志"\n'
        '    * "查看用户123的活动日志"\n'
        '    * "统计接口调用次数"\n\n'
        "4. **knowledge_query** - 需要查询知识图谱中的实体关系、推荐等时选择\n"
        "- 关键词：关系、推荐、关联、图谱、用户关系、相似文章等\n"
        "- 示例：\n"
        '    * "用户123收藏了哪些文章？"\n'
        '    * "推荐与这篇文章相似的内容"\n'
        '    * "查看用户关注链"\n'
        '    * "热门标签有哪些？"\n\n'
        "5. **general_chat** - 简单问候、闲聊、非功能性对话时选择\n"
        "- 关键词：你好、谢谢、再见、帮助等\n"
        "- 示例：\n"
        '    * "你好"\n'
        '    * "谢谢你的帮助"\n'
        '    * "你能做什么？"\n\n'
        "请只返回以下五个选项之一：database_query、article_search、log_analysis、knowledge_query、general_chat"
    )

    # ===== Agent 提示词模板 =====
    AGENT_PROMPT_TEMPLATE: str = (
        "你是一个中文 AI 助手，负责查询数据库信息、搜索文章内容、分析系统日志和使用知识图谱分析实体关系。\n\n"
        "你可以直接调用绑定好的工具，不需要手写 Thought/Action/Observation 这种文本格式。\n\n"
        "规则：\n"
        "1. 需要查询数据时优先使用工具，不要凭空猜测。\n"
        "2. 数据库统计和业务数据查询优先使用 SQL 工具，并尽量加上时间范围、用户范围、状态条件或 limit。\n"
        "3. 查询数据库表结构时，先确认真实表名，再执行查询；例如用户表是 user，不是 users。\n"
        "4. 涉及文章、用户、分类、标签之间的关系、相似文章和推荐时，优先使用 Neo4j 知识图谱工具。\n"
        "5. MongoDB 工具只用于日志相关查询，查询前先确认 collection 名称。\n"
        "6. 最终回答必须使用中文，简洁明确。\n\n"
        "当前问题：{input}"
    )

    CONTENT_SUMMARIZE_PROMPT: str = (
        "请对以下内容进行精要总结，提取关键信息和核心观点：\n\n"
        "原文内容：\n"
        "{content}\n\n"
        "要求：\n"
        "1. 总结长度控制在 {max_length} 字以内\n"
        "2. 提取核心要点和关键信息\n"
        "3. 保留最重要的细节\n"
        "4. 用清晰、凝练的语言表述"
    )

    REFERENCE_BASED_EVALUATION_PROMPT: str = (
        "请基于以下权威参考文本，对文章或内容进行评价。\n\n"
        "权威参考文本：\n"
        "{reference_content}\n\n"
        "请对以下内容进行评价，并给出评分：\n"
        "1. 给出简短的评价（100-200字），要求在评价中明确提及\"参考权威文本\"或\"基于权威文本\"等字眼\n"
        "2. 给出0-10分的评分（可以是小数）\n"
        "3. 请使用以下格式输出：\n"
        "    评价内容：[你的评价，需包含参考权威文本的相关表述]\n"
        "    评分：[你的评分]\n"
        "4. 评价内容中应清晰指出哪些观点与权威文本相符或不符\n\n"
        "待评价内容：\n"
        "{message}"
    )

    # ===== RAG 工具描述 =====
    RAG_TOOL_DESC: str = (
        "使用RAG(检索增强生成)搜索相关文章。"
        "根据用户问题，在向量数据库中搜索最相关的文章内容。"
        "适用于回答关于文章内容、技术知识、教程等问题。"
        "参数格式: 用户的问题或关键词(字符串)"
        "示例: \"如何使用Python进行数据分析\""
        "使用场景: 用户询问具体的技术问题、寻找相关文章、需要文章内容支持时使用。"
    )

    # ===== MongoDB 日志工具描述 =====
    MONGODB_LIST_COLLECTIONS_TOOL_DESC: str = (
        "列出 MongoDB 日志数据库中的所有 collection 及其基本信息。"
        "返回每个 collection 的记录数和样本字段，帮助确认可查询的数据集合。"
        "参数格式: 无参数。"
        "使用场景: 用户需要先了解日志库里有哪些 collection 以及大致字段结构时使用。"
    )
    MONGODB_QUERY_TOOL_DESC: str = (
        "MongoDB 日志查询工具，仅用于查询日志相关 collection。"
        "参数必须是 JSON 字符串，支持 collection_name、filter_dict、limit 三个字段。"
        '参数示例: {"collection_name": "api_logs", "limit": 10}'
        "使用场景: 已明确 collection 后，按条件查询 API 日志、错误日志、操作日志等数据时使用。"
        "如果日志量可能较大，必须加上时间范围、用户范围、状态条件或 limit。"
    )

    # ===== SQL 工具描述 =====
    SQL_TABLE_TOOL_DESC: str = (
        "获取MySQL数据库表结构信息。"
        "如果提供表名参数，返回该表的详细结构（列名、类型、主键、索引等）。"
        "如果不提供参数，返回所有表的列表和基本信息。"
        "参数格式: 表名(字符串)，如 'articles' 或 'users'，留空获取所有表。"
        "使用场景: 需要了解数据库结构、查询某表有哪些字段时使用。"
    )
    SQL_QUERY_TOOL_DESC: str = (
        "执行只读SQL查询并返回结果。"
        "只允许单条只读语句，例如 SELECT/WITH/SHOW/DESC/DESCRIBE/EXPLAIN。"
        "不允许 INSERT/UPDATE/DELETE/DDL/锁表/多语句 等任何修改或高风险操作。"
        "返回最多20行数据，以表格形式展示。"
        "参数格式: 完整的只读SQL语句。"
        '示例: "SELECT * FROM articles WHERE status=1 LIMIT 10"'
        "使用场景: 需要查询系统数据、业务数据、统计分析、获取具体记录时使用。"
        "如果涉及大表或可能返回大量数据，必须主动加上时间范围、用户范围、状态条件或 LIMIT。"
    )

    # ===== Neo4j 工具描述 =====
    NEO4J_PREDEFINED_QUERY_TOOL_DESC: str = (
        "执行预定义的 Neo4j 知识图谱查询。"
        "适用于文章详情、分类热门文章、作者文章、同分类相似文章、关注链推荐、热门文章、标签排行和个性化推荐。"
        "参数包含 query_name 和 params。优先使用预定义查询，limit 最大 50。"
    )
    NEO4J_CUSTOM_CYPHER_TOOL_DESC: str = (
        "执行自定义只读 Cypher 查询。"
        "图谱包含 User、Article、Category、SubCategory、Tag 节点，以及 PUBLISHED_BY、BELONGS_TO、BELONGS_TO_CATEGORY、TAGGED_AS、LIKES、COLLECTS、COMMENTED_ON、FOLLOWS 关系。"
        "仅允许 MATCH、OPTIONAL MATCH、WITH、RETURN 或 CALL db.* 类型的只读查询。"
    )

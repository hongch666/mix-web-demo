from typing import Literal
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


class IntentRouter:
    """意图识别路由器"""
    
    def __init__(self, llm):
        """
        初始化路由器
        
        Args:
            llm: LangChain LLM实例
        """
        # 延迟导入避免循环依赖
        from common.utils import fileLogger
        self.logger = fileLogger
        
        self.llm = llm
        
        # 创建意图识别提示词
        self.intent_prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个智能路由助手，需要判断用户的问题类型。

            分析用户问题，判断应该使用哪种方式处理：

            1. **database_query** - 需要查询数据库统计数据、获取记录列表、数据分析时选择
            - 关键词：多少、统计、列表、查询、总数、排行、最新、用户信息等
            - 示例：
                * "有多少篇文章？"
                * "最近发布的10篇文章"
                * "user_id为123的用户信息"
                * "各分类的文章数量统计"
                * "浏览量最高的文章"

            2. **article_search** - 需要搜索文章内容、技术知识、教程等时选择
            - 关键词：如何、怎么做、教程、学习、介绍、什么是、原理等
            - 示例：
                * "如何使用Python进行数据分析？"
                * "React Hooks的使用方法"
                * "什么是机器学习？"
                * "Docker容器化部署教程"
                * "数据库索引的原理"

            3. **general_chat** - 简单问候、闲聊、不需要查询数据的问题
            - 示例：
                * "你好"
                * "今天天气怎么样"
                * "你能做什么"

            请只返回以下三个选项之一：database_query、article_search、general_chat"""),
            ("human", "用户问题：{question}")
        ])
        
        # 创建链
        self.chain = self.intent_prompt | self.llm | StrOutputParser()
    
    def route(self, question: str) -> Literal["database_query", "article_search", "general_chat"]:
        """
        路由用户问题
        
        Args:
            question: 用户问题
            
        Returns:
            意图类型：database_query、article_search或general_chat
        """
        try:
            result = self.chain.invoke({"question": question}).strip().lower()
            
            # 标准化结果
            if "database" in result or "数据库" in result:
                intent = "database_query"
            elif "article" in result or "文章" in result or "search" in result:
                intent = "article_search"
            elif "general" in result or "chat" in result or "闲聊" in result:
                intent = "general_chat"
            else:
                # 默认使用文章搜索
                intent = "article_search"
            
            self.logger.info(f"意图识别结果: {question} -> {intent}")
            return intent
            
        except Exception as e:
            self.logger.error(f"意图识别失败: {e}, 默认使用article_search")
            return "article_search"
    
    def route_with_confidence(self, question: str) -> tuple[str, str]:
        """
        路由用户问题并返回置信度说明
        
        Args:
            question: 用户问题
            
        Returns:
            (意图类型, 原始响应)
        """
        try:
            raw_response = self.chain.invoke({"question": question}).strip()
            result = raw_response.lower()
            
            if "database" in result:
                return "database_query", raw_response
            elif "article" in result or "search" in result:
                return "article_search", raw_response
            elif "general" in result or "chat" in result:
                return "general_chat", raw_response
            else:
                return "article_search", raw_response
                
        except Exception as e:
            self.logger.error(f"意图识别失败: {e}")
            return "article_search", str(e)

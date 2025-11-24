from typing import List
from langchain_core.prompts import PromptTemplate
from sqlmodel import Session
from common.agent import get_sql_tools, get_rag_tools
from common.utils.writeLog import fileLogger as logger
from api.mapper import AiHistoryMapper


# ========== 共享的Agent Prompt模板 ==========
AGENT_PROMPT_TEMPLATE = """你是一个智能助手，可以帮助用户查询数据库信息和搜索文章内容。

你有以下工具可以使用:
{tools}

工具名称: {tool_names}

使用以下格式回答问题:

Question: 用户的问题
Thought: 你需要思考应该做什么
Action: 选择一个工具，必须是 [{tool_names}] 中的一个
Action Input: 工具的输入参数
Observation: 工具执行的结果
... (这个 Thought/Action/Action Input/Observation 可以重复N次)
Thought: 我现在知道最终答案了
Final Answer: 给用户的最终回答

重要提示 - 如何选择和组合工具:
1. 数据统计/统计查询: 优先使用 get_table_schema 查看表结构，然后用 execute_sql_query 执行SQL查询
示例: "有多少篇文章"、"发布最多的作者是谁"、"文章总浏览量"

2. 文章内容/技术知识查询: 使用 search_articles 搜索相关文章
示例: "Python最佳实践"、"如何学习机器学习"、"深度学习教程"

3. 组合查询 - 需要同时使用多个工具:
示例: "一共有多少篇文章，并且推荐一些人工智能相关的文章"
处理方式:
- 第1步: 用 execute_sql_query 查询文章总数
- 第2步: 用 search_articles 搜索"人工智能"相关文章

示例: "统计有多少个用户，并查找一些关于Python的教程文章"
处理方式:
- 第1步: 用 execute_sql_query 查询用户总数
- 第2步: 用 search_articles 搜索"Python教程"

示例: "按分类统计文章数，并推荐技术文章"
处理方式:
- 第1步: 用 execute_sql_query 查询各分类文章数
- 第2步: 用 search_articles 搜索"技术"相关文章

关键特点:
- 你可以根据需要多次使用工具，包括同时使用SQL和RAG工具
- 优先识别用户问题中包含多个子问题或信息需求的情况
- 对于组合问题，分步骤调用不同的工具，不要试图用一个工具完成所有工作
- 始终用中文回答用户
- 如果一个工具返回的结果不足或没有匹配文本，尝试使用其他工具补充信息
- 如果RAG返回"未找到相关文章"或"没有匹配的内容"，告知用户系统中没有相关内容

开始!

Question: {input}
Thought: {agent_scratchpad}"""


def get_agent_prompt() -> PromptTemplate:
    """获取Agent的Prompt模板"""
    return PromptTemplate.from_template(AGENT_PROMPT_TEMPLATE)


def initialize_ai_tools():
    """初始化AI工具
    
    Returns:
        tuple: (sql_tools, rag_tools, all_tools)
    """
    try:
        sql_tools_instance = get_sql_tools()
        rag_tools_instance = get_rag_tools()
        
        sql_tools = sql_tools_instance.get_langchain_tools()
        rag_tools = rag_tools_instance.get_langchain_tools()
        all_tools = sql_tools + rag_tools
        
        return sql_tools_instance, rag_tools_instance, all_tools
    except Exception as e:
        logger.error(f"初始化AI工具失败: {e}")
        raise


class BaseAiService:
    """AI服务基类"""
    
    def __init__(self, ai_history_mapper: "AiHistoryMapper", service_name: str = "AI"):
        self.ai_history_mapper = ai_history_mapper
        self.service_name = service_name
        self.llm = None
        self.agent_executor = None
        self.intent_router = None
        self.all_tools = []
    
    def _load_chat_history(self, user_id: int, db: Session) -> List[tuple]:
        """从数据库加载聊天历史"""
        try:
            histories = self.ai_history_mapper.get_all_ai_history_by_userid(
                db, user_id=user_id, limit=5
            )
            chat_history = []
            for h in histories:
                chat_history.append((h.ask, h.reply))
            return chat_history
        except Exception as e:
            logger.error(f"加载聊天历史失败: {e}")
            return []
    
    def _build_thinking_text(self, intermediate_steps: list) -> str:
        """构建思考过程文本
        
        Args:
            intermediate_steps: Agent的中间步骤列表
            
        Returns:
            str: 格式化的思考过程文本
        """
        thinking_text = ""
        if intermediate_steps:
            thinking_text = "Agent 执行过程:\n"
            for i, (action, observation) in enumerate(intermediate_steps, 1):
                tool_name = action.tool if hasattr(action, 'tool') else str(action)
                tool_input = action.tool_input if hasattr(action, 'tool_input') else ""
                thinking_text += f"\n步骤 {i}:\n"
                thinking_text += f"  工具: {tool_name}\n"
                thinking_text += f"  输入: {tool_input}\n"
                thinking_text += f"  结果: {observation}\n"
        return thinking_text
    
    def _build_chat_context(self, chat_history: List[tuple]) -> str:
        """构建聊天历史上下文
        
        Args:
            chat_history: 聊天历史列表
            
        Returns:
            str: 格式化的历史对话上下文
        """
        context = ""
        if chat_history:
            context = "\n\n历史对话:\n" + "\n".join(
                [f"用户: {h}\nAI: {a}" for h, a in chat_history[-3:]]
            ) + "\n\n"
        return context

from typing import List, Optional
from langchain_core.prompts import PromptTemplate
from sqlmodel import Session
from common.agent import get_sql_tools, get_rag_tools, get_mongodb_tools
from common.utils.writeLog import fileLogger as logger

# ========== 共享的Prompt模板 ==========

# 内容总结提示词
CONTENT_SUMMARIZE_PROMPT = """请对以下内容进行精要总结，提取关键信息和核心观点：

原文内容：
{content}

要求：
1. 总结长度控制在 {max_length} 字以内
2. 提取核心要点和关键信息
3. 保留最重要的细节
4. 用清晰、凝练的语言表述
"""

# 基于参考文本的评价提示词
REFERENCE_BASED_EVALUATION_PROMPT = """请基于以下权威参考文本，对文章或内容进行评价。

权威参考文本：
{reference_content}

请对以下内容进行评价，并给出评分：
1. 给出简短的评价（100-200字）
2. 给出0-10分的评分（可以是小数）
3. 请使用以下格式输出：
    评价内容：[你的评价]
    评分：[你的评分]

待评价内容：
{message}
"""

# AI 助手的Agent提示词模板
AGENT_PROMPT_TEMPLATE = """你是一个智能助手，可以帮助用户查询数据库信息、搜索文章内容和分析系统日志。

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

重要提示 - 如何选择和使用工具:

1. 数据统计/统计查询: 优先使用 get_table_schema 查看表结构，然后用 execute_sql_query 执行SQL查询
   示例: "有多少篇文章"、"发布最多的作者是谁"、"文章总浏览量"

2. 文章内容/技术知识查询: 使用 search_articles 搜索相关文章
   示例: "Python最佳实践"、"如何学习机器学习"、"深度学习教程"

3. MongoDB 日志和系统分析: 使用以下两个工具

   第一步: 使用 list_mongodb_collections 列出所有可用的 collection
   - 这会告诉你有哪些数据集合可以查询（如 api_logs, error_logs 等）
   - 以及每个 collection 中有哪些字段
   - Action Input: (无需参数)

   第二步: 使用 query_mongodb 查询特定 collection
   Action Input 必须是 JSON 格式字符串，包含以下参数:
   - collection_name: 必需，collection 的名称 (字符串)
   - filter_dict: 可选，MongoDB 查询条件 (JSON对象)
   - limit: 可选，返回结果数量限制 (整数，默认10)
   
   Action Input 示例:
   - 查询 api_logs 的前10条: {{"collection_name": "api_logs", "limit": 10}}
   - 查询特定用户的 api_logs: {{"collection_name": "api_logs", "filter_dict": {{"user_id": 122}}, "limit": 20}}
   - 查询错误日志: {{"collection_name": "error_logs", "limit": 10}}
   - 查询文章日志: {{"collection_name": "articlelogs", "limit": 10}}

4. 工作流程建议:
   - 如果用户问关于"日志"、"记录"、"API请求"、"错误"等：
     1) 首先调用 list_mongodb_collections 查看有哪些 collection
     2) 然后根据结果调用 query_mongodb 查询具体数据
   
   - 对于简单查询（如"最近的API请求"）：
     直接使用 query_mongodb，传递 JSON 参数

关键特点:
- 你可以根据需要多次使用工具
- 对于组合问题，分步骤调用不同的工具
- 始终用中文回答用户
- MongoDB 的 filter_dict 支持完整的 MongoDB 查询语法，如 $gte, $lte, $regex 等
- 如果查询返回空结果，可以尝试修改查询条件或查询其他 collection
- Action Input 必须是有效的 JSON 字符串，不能是 Python 字典

开始!

Question: {input}
Thought: {agent_scratchpad}"""

def get_agent_prompt() -> PromptTemplate:
    """获取Agent的Prompt模板"""
    return PromptTemplate.from_template(AGENT_PROMPT_TEMPLATE)

def initialize_ai_tools(user_id: Optional[int] = None, db: Optional[Session] = None, include_sql: bool = True, include_logs: bool = True):
    """初始化AI工具，支持基于权限的工具选择
    
    Args:
        user_id: 用户ID（用于权限检查）
        db: 数据库会话（用于权限检查）
        include_sql: 是否包含 SQL 工具
        include_logs: 是否包含 MongoDB 日志工具
    
    Returns:
        tuple: (sql_tools_instance, rag_tools_instance, mongodb_log_tools_instance, all_tools)
    """
    try:
        sql_tools_instance = None
        rag_tools_instance = None
        mongodb_log_tools_instance = None
        all_tools = []
        
        # 获取 SQL 工具
        if include_sql:
            try:
                sql_tools_instance = get_sql_tools()
                sql_tools = sql_tools_instance.get_langchain_tools()
                all_tools.extend(sql_tools)
                logger.info(f"已加载 SQL 工具: {len(sql_tools)} 个")
            except Exception as e:
                logger.warning(f"加载 SQL 工具失败: {e}")
        
        # 获取 RAG 工具
        try:
            rag_tools_instance = get_rag_tools()
            rag_tools = rag_tools_instance.get_langchain_tools()
            all_tools.extend(rag_tools)
            logger.info(f"已加载 RAG 工具: {len(rag_tools)} 个")
        except Exception as e:
            logger.warning(f"加载 RAG 工具失败: {e}")
        
        # 获取 MongoDB 日志工具
        if include_logs:
            try:
                mongodb_tools_instance = get_mongodb_tools()
                mongodb_tools = mongodb_tools_instance.get_langchain_tools()
                all_tools.extend(mongodb_tools)
                logger.info(f"已加载 MongoDB 日志工具: {len(mongodb_tools)} 个")
            except Exception as e:
                logger.warning(f"加载 MongoDB 日志工具失败: {e}")
        
        logger.info(f"总共加载了 {len(all_tools)} 个工具")
        return sql_tools_instance, rag_tools_instance, mongodb_log_tools_instance, all_tools
    except Exception as e:
        logger.error(f"初始化AI工具失败: {e}")
        raise

class BaseAiService:
    """AI服务基类"""
    
    def __init__(self, ai_history_mapper, service_name: str = "AI"):
        self.ai_history_mapper = ai_history_mapper
        self.service_name = service_name
        self.llm = None
        self.agent_executor = None
        self.intent_router = None
        self.all_tools = []
    
    def _get_summarize_prompt(self, content: str, max_length: int = 1000) -> str:
        """获取内容总结提示词
        
        Args:
            content: 需要总结的内容
            max_length: 最大总结长度
            
        Returns:
            str: 格式化后的提示词
        """
        return CONTENT_SUMMARIZE_PROMPT.format(
            content=content,
            max_length=max_length
        )
    
    def _get_reference_evaluation_prompt(self, message: str, reference_content: str) -> str:
        """获取基于参考文本的评价提示词
        
        Args:
            message: 待评价内容
            reference_content: 权威参考文本
            
        Returns:
            str: 格式化后的提示词
        """
        return REFERENCE_BASED_EVALUATION_PROMPT.format(
            reference_content=reference_content,
            message=message
        )
    
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
    
    def _build_complete_thinking_text(self, intermediate_steps: list, final_result: str = "") -> str:
        """构建完整的思考过程文本（包含最终结果）
        
        Args:
            intermediate_steps: Agent的中间步骤列表
            final_result: Agent的最终结果
            
        Returns:
            str: 完整的思考过程文本
        """
        thinking_parts = []
        
        # 构建中间步骤
        if intermediate_steps:
            thinking_parts.append("Agent 执行过程:\n")
            for i, (action, observation) in enumerate(intermediate_steps, 1):
                tool_name = action.tool if hasattr(action, 'tool') else str(action)
                tool_input = action.tool_input if hasattr(action, 'tool_input') else ""
                
                step_text = f"\n步骤 {i}:\n"
                step_text += f"  工具: {tool_name}\n"
                step_text += f"  输入: {tool_input}\n"
                step_text += f"  结果: {observation}\n"
                
                thinking_parts.append(step_text)
        
        # 添加最终结果
        if final_result:
            thinking_parts.append(f"\n\n最终分析结果:\n{final_result}")
        
        # 拼接所有部分
        complete_text = "".join(thinking_parts)
        return complete_text
    
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

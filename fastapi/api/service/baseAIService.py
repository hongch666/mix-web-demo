from typing import List, Optional, Any, Tuple
from langchain_core.prompts import PromptTemplate
from sqlmodel import Session
from common.agent import get_sql_tools, get_rag_tools, get_mongodb_tools
from common.utils import fileLogger as logger, Constants

def get_agent_prompt() -> PromptTemplate:
    """获取Agent的Prompt模板"""
    return PromptTemplate.from_template(Constants.AGENT_PROMPT_TEMPLATE)

def initialize_ai_tools(
    include_sql: bool = True, 
    include_logs: bool = True
) -> Tuple[Optional[Any], Optional[Any], Optional[Any], List[Any]]:
    """初始化AI工具，支持基于权限的工具选择
    
    Args:
        user_id: 用户ID（用于权限检查）
        db: 数据库会话（用于权限检查）
        include_sql: 是否包含 SQL 工具
        include_logs: 是否包含 MongoDB 日志工具
    
    Returns:
        tuple: (sql_tools_instance, rag_tools_instance, mongodb_log_tools_instance, all_tools)
    """
    sql_tools_instance: Optional[Any] = None
    rag_tools_instance: Optional[Any] = None
    mongodb_tools_instance: Optional[Any] = None
    all_tools: List[Any] = []
    
    # 获取 SQL 工具
    if include_sql:
        try:
            sql_tools_instance = get_sql_tools()
            sql_tools: List[Any] = sql_tools_instance.get_langchain_tools()
            all_tools.extend(sql_tools)
            logger.info(f"已加载 SQL 工具: {len(sql_tools)} 个")
        except Exception as e:
            logger.warning(f"加载 SQL 工具失败: {e}")
    
    # 获取 RAG 工具
    try:
        rag_tools_instance = get_rag_tools()
        rag_tools: List[Any] = rag_tools_instance.get_langchain_tools()
        all_tools.extend(rag_tools)
        logger.info(f"已加载 RAG 工具: {len(rag_tools)} 个")
    except Exception as e:
        logger.warning(f"加载 RAG 工具失败: {e}")
    
    # 获取 MongoDB 日志工具
    if include_logs:
        try:
            mongodb_tools_instance = get_mongodb_tools()
            mongodb_tools: List[Any] = mongodb_tools_instance.get_langchain_tools()
            all_tools.extend(mongodb_tools)
            logger.info(f"已加载 MongoDB 日志工具: {len(mongodb_tools)} 个")
        except Exception as e:
            logger.warning(f"加载 MongoDB 日志工具失败: {e}")
    
    logger.info(f"总共加载了 {len(all_tools)} 个工具")
    return sql_tools_instance, rag_tools_instance, mongodb_tools_instance, all_tools

class BaseAiService:
    """AI服务基类"""
    
    def __init__(self, ai_history_mapper: Any, service_name: str = "AI") -> None:
        self.ai_history_mapper: Any = ai_history_mapper
        self.service_name: str = service_name
        self.llm: Optional[Any] = None
        self.agent: Optional[Any] = None
        self.agent_executor: Optional[Any] = None
        self.intent_router: Optional[Any] = None
        self.all_tools: List[Any] = []
    
    def _get_summarize_prompt(self, content: str, max_length: int = 1000) -> str:
        """获取内容总结提示词
        
        Args:
            content: 需要总结的内容
            max_length: 最大总结长度
            
        Returns:
            str: 格式化后的提示词
        """
        return Constants.CONTENT_SUMMARIZE_PROMPT.format(
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
        return Constants.REFERENCE_BASED_EVALUATION_PROMPT.format(
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

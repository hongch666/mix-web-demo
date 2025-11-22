from functools import lru_cache
from typing import AsyncGenerator, Optional, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_classic.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate
from fastapi import Depends
from sqlmodel import Session
from api.mapper import AiHistoryMapper, get_ai_history_mapper
from common.agent import get_sql_tools, get_rag_tools
from common.agent.intent_router import IntentRouter
from common.utils import fileLogger as logger
from config import load_config, load_secret_config


class TongyiService:
    def __init__(self, ai_history_mapper: AiHistoryMapper):
        self.ai_history_mapper = ai_history_mapper
        
        # 初始化通义千问客户端
        try:
            tongyi_cfg = load_config("tongyi") or {}
            tongyi_secret = load_secret_config("tongyi") or {}
            self._api_key: str = tongyi_secret.get("api_key")
            self._model_name: str = tongyi_cfg.get("model_name", "qwen-flash")
            self._base_url: str = tongyi_cfg.get("base_url", "https://dashscope.aliyuncs.com/compatible-mode/v1")
            self._timeout: int = tongyi_cfg.get("timeout", 30)
            
            if self._api_key:
                self.llm = ChatOpenAI(
                    model=self._model_name,
                    openai_api_key=self._api_key,
                    openai_api_base=self._base_url,
                    temperature=0.7,
                    timeout=self._timeout,
                )
                
                # 初始化工具
                try:
                    self.sql_tools_instance = get_sql_tools()
                    self.rag_tools_instance = get_rag_tools()
                    
                    # 获取工具列表
                    sql_tools = self.sql_tools_instance.get_langchain_tools()
                    rag_tools = self.rag_tools_instance.get_langchain_tools()
                    self.all_tools = sql_tools + rag_tools
                    
                    # 初始化意图路由器
                    self.intent_router = IntentRouter(self.llm)
                    
                    # 创建Agent的Prompt
                    agent_prompt = PromptTemplate.from_template("""你是一个智能助手，可以帮助用户查询数据库信息和搜索文章内容。

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
Thought: {agent_scratchpad}""")
                    
                    # 创建ReAct Agent
                    self.agent = create_react_agent(
                        llm=self.llm,
                        tools=self.all_tools,
                        prompt=agent_prompt
                    )
                    
                    self.agent_executor = AgentExecutor(
                        agent=self.agent,
                        tools=self.all_tools,
                        verbose=True,
                        handle_parsing_errors=True,
                        max_iterations=5,
                        return_intermediate_steps=True
                    )
                    
                    logger.info("通义千问Agent服务初始化完成")
                except Exception as tool_error:
                    logger.warning(f"工具初始化部分失败: {tool_error}, 降级为基础对话模式")
                    self.agent_executor = None
                    self.intent_router = None
            else:
                self.llm = None
                self.agent_executor = None
                self.intent_router = None
                logger.warning("通义千问配置不完整，客户端未初始化")
        except Exception as e:
            self.llm = None
            self.agent_executor = None
            self.intent_router = None
            logger.error(f"初始化通义千问客户端失败: {e}")
    
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
    
    async def basic_chat(self, message: str) -> str:
        """最基础的对话接口 - 不使用知识库和向量数据库"""
        try:
            logger.info(f"基础对话: {message}")
            
            if not getattr(self, 'llm', None):
                return "聊天服务未配置或初始化失败"
            
            # 使用 LangChain 调用
            messages = [
                SystemMessage(content="你是一个中文AI助手，用于提供文章和博客推荐及分析系统数据。"),
                HumanMessage(content=message)
            ]
            response = await self.llm.ainvoke(messages)
            
            content: str = response.content
            logger.info(f"通义千问基础回复长度: {len(content)} 字符")
            return content
                
        except Exception as e:
            logger.error(f"通义千问基础对话异常: {str(e)}")
            return f"对话服务异常: {str(e)}"

    async def simple_chat(self, message: str, user_id: int = 0, db: Optional[Session] = None) -> str:
        """增强的聊天接口 - 使用Agent和RAG"""
        try:
            logger.info(f"用户 {user_id} 发送消息: {message}")
            
            if not getattr(self, 'llm', None):
                return "聊天服务未配置或初始化失败"
            
            # 如果Agent未初始化，降级为基础对话
            if not self.agent_executor:
                return await self.basic_chat(message)
            
            # 1. 意图识别（仅用于判断是否需要工具）
            intent = "general_chat"
            if self.intent_router:
                intent = self.intent_router.route(message)
                logger.info(f"识别意图: {intent}")
            
            # 2. 加载聊天历史
            chat_history = []
            if db and user_id:
                chat_history = self._load_chat_history(user_id, db)
            
            # 3. 根据意图选择处理方式
            if intent == "general_chat":
                # 简单闲聊，直接回复
                history_messages = []
                for human_msg, ai_msg in chat_history:
                    history_messages.append(HumanMessage(content=human_msg))
                    history_messages.append(AIMessage(content=ai_msg))
                
                messages = [
                    SystemMessage(content="你是一个友好的中文AI助手。"),
                    *history_messages,
                    HumanMessage(content=message)
                ]
                response = await self.llm.ainvoke(messages)
                result = response.content
                
            else:
                # 使用Agent处理，让Agent自己决定使用哪些工具
                # Agent可以同时调用SQL工具和RAG工具，或只调用其中一个
                logger.info("使用Agent处理，可同时调用SQL和RAG工具")
                
                # 添加历史上下文到输入
                context = ""
                if chat_history:
                    context = "\n\n历史对话:\n" + "\n".join(
                        [f"用户: {h}\nAI: {a}" for h, a in chat_history[-3:]]
                    ) + "\n\n"
                
                full_input = context + f"当前问题: {message}"
                
                agent_response = await self.agent_executor.ainvoke({"input": full_input})
                result = agent_response.get("output", "无法获取结果")
            
            logger.info(f"通义千问回复长度: {len(result)} 字符")
            return result
                
        except Exception as e:
            logger.error(f"通义千问聊天异常: {str(e)}")
            if "invalid" in str(e).lower() and "key" in str(e).lower():
                return "API密钥无效。请检查通义千问API密钥配置。"
            elif "quota" in str(e).lower() or "exceeded" in str(e).lower():
                return "API配额已超限。请稍后重试或检查配额设置。"
            elif "rate" in str(e).lower() and "limit" in str(e).lower():
                return "API调用频率超限。请稍后重试。"
            return f"聊天服务异常: {str(e)}"
        
    async def stream_chat(self, message: str, user_id: int = 0, db: Optional[Session] = None) -> AsyncGenerator[str, None]:
        """流式聊天接口
        
        Yields:
            dict 格式: {"type": "tool_call|thinking|content", "content": "..."}
            或直接返回字符串（向后兼容）
        """
        try:
            logger.info(f"用户 {user_id} 开始流式聊天: {message}")
            
            if not getattr(self, 'llm', None):
                yield {"type": "error", "content": "聊天服务未配置或初始化失败"}
                return
            
            # 如果Agent未初始化，降级为基础流式对话
            if not self.agent_executor:
                # 加载聊天历史
                chat_history = []
                if db and user_id:
                    chat_history = self._load_chat_history(user_id, db)
                
                # 构建消息
                history_messages = []
                for human_msg, ai_msg in chat_history:
                    history_messages.append(HumanMessage(content=human_msg))
                    history_messages.append(AIMessage(content=ai_msg))
                
                messages = [
                    SystemMessage(content="你是一个中文AI助手，用于提供文章和博客推荐及分析系统数据。"),
                    *history_messages,
                    HumanMessage(content=message)
                ]
                
                async for chunk in self.llm.astream(messages):
                    try:
                        if chunk.content:
                            logger.debug(f"收到流式内容块，长度: {len(chunk.content)} 字符")
                            yield {"type": "content", "content": chunk.content}
                    except Exception as chunk_error:
                        logger.error(f"处理流式内容块异常: {str(chunk_error)}")
                        continue
                return
            
            # 1. 意图识别（仅用于判断是否需要工具）
            intent = "general_chat"
            if self.intent_router:
                intent = self.intent_router.route(message)
                logger.info(f"识别意图: {intent}")
            
            # 2. 加载聊天历史
            chat_history = []
            if db and user_id:
                chat_history = self._load_chat_history(user_id, db)
            
            # 3. 根据意图选择处理方式
            if intent == "general_chat":
                # 简单闲聊，直接流式回复
                history_messages = []
                for human_msg, ai_msg in chat_history:
                    history_messages.append(HumanMessage(content=human_msg))
                    history_messages.append(AIMessage(content=ai_msg))
                
                messages = [
                    SystemMessage(content="你是一个友好的中文AI助手。"),
                    *history_messages,
                    HumanMessage(content=message)
                ]
                
                async for chunk in self.llm.astream(messages):
                    try:
                        if chunk.content:
                            yield {"type": "content", "content": chunk.content}
                    except Exception as chunk_error:
                        logger.error(f"处理流式内容块异常: {str(chunk_error)}")
                        continue
                
            else:
                # 使用Agent处理获取信息,然后流式输出最终答案
                logger.info("使用Agent处理,可同时调用SQL和RAG工具")
                
                # 添加历史上下文到输入
                context = ""
                if chat_history:
                    context = "\n\n历史对话:\n" + "\n".join(
                        [f"用户: {h}\nAI: {a}" for h, a in chat_history[-3:]]
                    ) + "\n\n"
                
                full_input = context + f"当前问题: {message}"
                
                # 第一步: 使用Agent获取信息和思考
                logger.info("Agent开始处理...")
                agent_response = await self.agent_executor.ainvoke({"input": full_input})
                agent_result = agent_response.get("output", "无法获取结果")
                
                # 提取中间步骤（工具调用）
                intermediate_steps = agent_response.get("intermediate_steps", [])
                
                # 构建完整的思考过程（不再单独输出工具调用）
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
                else:
                    thinking_text = agent_result
                
                # 输出 Agent 的完整思考过程
                yield {"type": "thinking", "content": thinking_text}
                
                # 第二步: 基于Agent的结果,流式生成更好的回答
                logger.info("Agent思考完成,开始流式输出优化后的答案")
                
                # 构建包含Agent思考结果的提示
                history_messages = []
                for human_msg, ai_msg in chat_history:
                    history_messages.append(HumanMessage(content=human_msg))
                    history_messages.append(AIMessage(content=ai_msg))
                
                stream_messages = [
                    SystemMessage(content="你是一个友好的中文AI助手。根据提供的信息,用流畅、自然的语言回答用户问题。"),
                    *history_messages,
                    HumanMessage(content=f"用户问题: {message}\n\n我已经获取到以下信息:\n{agent_result}\n\n请基于这些信息,用清晰、友好的方式回答用户的问题。")
                ]
                
                async for chunk in self.llm.astream(stream_messages):
                    try:
                        if chunk.content:
                            yield {"type": "content", "content": chunk.content}
                    except Exception as chunk_error:
                        logger.error(f"处理流式内容块异常: {str(chunk_error)}")
                        continue
                    
        except Exception as e:
            logger.error(f"流式聊天异常: {str(e)}")
            if "invalid" in str(e).lower() and "key" in str(e).lower():
                yield {"type": "error", "content": "API密钥无效。请检查通义千问API密钥配置。"}
            elif "quota" in str(e).lower() or "exceeded" in str(e).lower():
                yield {"type": "error", "content": "API配额已超限。请稍后重试或检查配额设置。"}
            elif "rate" in str(e).lower() and "limit" in str(e).lower():
                yield {"type": "error", "content": "API调用频率超限。请稍后重试。"}
            else:
                yield {"type": "error", "content": f"流式聊天服务异常: {str(e)}"}


@lru_cache()
def get_tongyi_service(ai_history_mapper: AiHistoryMapper = Depends(get_ai_history_mapper)) -> TongyiService:
    """获取通义千问服务单例实例"""
    return TongyiService(ai_history_mapper)

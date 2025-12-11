from functools import lru_cache
from typing import AsyncGenerator, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_classic.agents import AgentExecutor, create_react_agent
from fastapi import Depends
from sqlmodel import Session
from api.mapper import AiHistoryMapper, get_ai_history_mapper, UserMapper, get_user_mapper
from common.utils.baseAIService import BaseAiService, get_agent_prompt, initialize_ai_tools
from common.agent.intentRouter import IntentRouter
from common.agent.userPermissionManager import UserPermissionManager
from common.middleware import get_current_user_id
from common.utils import fileLogger as logger
from config import load_config, load_secret_config


class QwenService(BaseAiService):
    def __init__(self, ai_history_mapper: AiHistoryMapper, user_mapper: Optional[UserMapper] = None):
        super().__init__(ai_history_mapper, service_name="Qwen")
        
        # 初始化权限管理器
        self.perm_manager = UserPermissionManager(user_mapper)
        
        # 初始化通义千问客户端
        try:
            qwen_cfg = load_config("qwen") or {}
            qwen_secret = load_secret_config("qwen") or {}
            self._api_key: str = qwen_secret.get("api_key")
            self._model_name: str = qwen_cfg.get("model_name", "qwen-flash")
            self._base_url: str = qwen_cfg.get("base_url", "https://dashscope.aliyuncs.com/compatible-mode/v1")
            self._timeout: int = qwen_cfg.get("timeout", 30)
            
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
                    _, _, _, self.all_tools = initialize_ai_tools()
                    
                    # 初始化意图路由器（传递 user_mapper）
                    self.intent_router = IntentRouter(self.llm, user_mapper=user_mapper)
                    
                    # 创建ReAct Agent
                    agent_prompt = get_agent_prompt()
                    
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
                    
                    logger.info("Qwen Agent服务初始化完成")
                except Exception as tool_error:
                    logger.warning(f"工具初始化部分失败: {tool_error}, 降级为基础对话模式")
                    self.agent_executor = None
                    self.intent_router = None
            else:
                self.llm = None
                self.agent_executor = None
                self.intent_router = None
                logger.warning("Qwen配置不完整，客户端未初始化")
        except Exception as e:
            self.llm = None
            self.agent_executor = None
            self.intent_router = None
            logger.error(f"初始化Qwen客户端失败: {e}")
    
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
            logger.info(f"Qwen基础回复长度: {len(content)} 字符")
            return content
                
        except Exception as e:
            logger.error(f"Qwen基础对话异常: {str(e)}")
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
            
            # 1. 权限检查（如果有用户ID和数据库会话）
            intent = "general_chat"
            if self.intent_router and db and user_id:
                intent, has_permission, error_msg = self.intent_router.route_with_permission_check(message, user_id, db)
                logger.info(f"识别意图: {intent}, 有权限: {has_permission}")
                
                # 如果没有权限，返回错误信息
                if not has_permission:
                    logger.warning(f"用户 {user_id} 无权限访问: {intent}")
                    return error_msg
            elif self.intent_router:
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
                context = self._build_chat_context(chat_history)
                full_input = context + f"当前问题: {message}"
                
                agent_response = await self.agent_executor.ainvoke({"input": full_input})
                result = agent_response.get("output", "无法获取结果")
            
            logger.info(f"Qwen回复长度: {len(result)} 字符")
            return result
                
        except Exception as e:
            logger.error(f"Qwen聊天异常: {str(e)}")
            if "invalid" in str(e).lower() and "key" in str(e).lower():
                return "API密钥无效。请检查Qwen API密钥配置。"
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
            
            # 1. 权限检查（如果有用户ID和数据库会话）
            intent = "general_chat"
            if self.intent_router and db and user_id:
                intent, has_permission, error_msg = self.intent_router.route_with_permission_check(message, user_id, db)
                logger.info(f"识别意图: {intent}, 有权限: {has_permission}")
                
                # 如果没有权限，返回错误信息
                if not has_permission:
                    logger.warning(f"用户 {user_id} 无权限访问: {intent}")
                    yield {"type": "error", "content": error_msg}
                    return
            elif self.intent_router:
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
                context = self._build_chat_context(chat_history)
                full_input = context + f"当前问题: {message}"
                
                # 第一步: 使用Agent获取信息和思考
                logger.info("Agent开始处理...")
                agent_response = await self.agent_executor.ainvoke({"input": full_input})
                agent_result = agent_response.get("output", "无法获取结果")
                
                # 提取中间步骤（工具调用）
                intermediate_steps = agent_response.get("intermediate_steps", [])
                
                # 构建完整的思考过程（包含所有中间步骤和最终结果）
                thinking_text = self._build_complete_thinking_text(intermediate_steps, agent_result)
                
                logger.info(f"思考过程长度: {len(thinking_text)} 字符")
                # 记录完整的思考内容用于调试
                if len(thinking_text) > 5000:
                    logger.debug(f"思考过程内容（前2000字）: {thinking_text[:2000]}")
                    logger.debug(f"思考过程内容（中间2000字）: {thinking_text[len(thinking_text)//2-1000:len(thinking_text)//2+1000]}")
                    logger.debug(f"思考过程内容（末尾2000字）: {thinking_text[-2000:]}")
                else:
                    logger.debug(f"完整思考过程: {thinking_text}")
                
                # 一次性输出完整的思考过程（不分块，确保完整）
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
                yield {"type": "error", "content": "API密钥无效。请检查Qwen API密钥配置。"}
            elif "quota" in str(e).lower() or "exceeded" in str(e).lower():
                yield {"type": "error", "content": "API配额已超限。请稍后重试或检查配额设置。"}
            elif "rate" in str(e).lower() and "limit" in str(e).lower():
                yield {"type": "error", "content": "API调用频率超限。请稍后重试。"}
            else:
                yield {"type": "error", "content": f"流式聊天服务异常: {str(e)}"}


@lru_cache()
def get_qwen_service(
    ai_history_mapper: AiHistoryMapper = Depends(get_ai_history_mapper),
    user_mapper: UserMapper = Depends(get_user_mapper)
) -> QwenService:
    """获取Qwen服务单例实例"""
    return QwenService(ai_history_mapper, user_mapper)

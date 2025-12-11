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


class DoubaoService(BaseAiService):
    def __init__(self, ai_history_mapper: AiHistoryMapper, user_mapper: Optional[UserMapper] = None):
        super().__init__(ai_history_mapper, service_name="Doubao")
        
        # 初始化权限管理器
        self.perm_manager = UserPermissionManager(user_mapper)
        
        # 初始化豆包客户端
        try:
            doubao_cfg = load_config("doubao") or {}
            doubao_secret = load_secret_config("doubao") or {}
            self._api_key: str = doubao_secret.get("api_key")
            self._model: str = doubao_cfg.get("model")
            self._base_url: str = doubao_cfg.get("base_url")
            self._timeout: int = doubao_cfg.get("timeout", 60)
            
            if self._api_key and self._base_url:
                self.llm = ChatOpenAI(
                    model=self._model,
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
                    
                    logger.info("豆包Agent服务初始化完成")
                except Exception as tool_error:
                    logger.warning(f"工具初始化部分失败: {tool_error}, 降级为基础对话模式")
                    self.agent_executor = None
                    self.intent_router = None
            else:
                self.llm = None
                self.agent_executor = None
                self.intent_router = None
                logger.warning("豆包配置不完整，客户端未初始化")
        except Exception as e:
            self.llm = None
            self.agent_executor = None
            self.intent_router = None
            logger.error(f"初始化豆包客户端失败: {e}")

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
            result: str = response.content
            logger.info(f"豆包基础回复长度: {len(result)} 字符")
            return result
            
        except Exception as e:
            logger.error(f"豆包基础对话异常: {str(e)}")
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
            permission_info = ""
            if self.intent_router and db and user_id:
                intent, has_permission, permission_msg = self.intent_router.route_with_permission_check(message, user_id, db)
                logger.info(f"识别意图: {intent}, 有权限: {has_permission}")
                
                # 如果没有权限，作为信息传递给AI而不是直接返回
                if not has_permission:
                    logger.info(f"用户 {user_id} 无权限访问: {intent}")
                    permission_info = f"[权限提示: {permission_msg}]" if permission_msg else "[权限提示: 您没有权限访问此功能]"
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
                # 如果有权限限制信息，将其添加到输入中供AI参考
                full_input = context + f"{permission_info}当前问题: {message}"
                
                agent_response = await self.agent_executor.ainvoke({"input": full_input})
                result = agent_response.get("output", "无法获取结果")
            
            logger.info(f"豆包回复长度: {len(result)} 字符")
            return result
            
        except Exception as e:
            logger.error(f"豆包聊天异常: {str(e)}")
            return f"聊天服务异常: {str(e)}"
        
    async def stream_chat(self, message: str, user_id: int = 0, db: Optional[Session] = None) -> AsyncGenerator[str, None]:
        """流式聊天接口
        
        Yields:
            dict 格式: {"type": "thinking|content|error", "content": "..."}
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
            permission_info = ""
            if self.intent_router and db and user_id:
                intent, has_permission, permission_msg = self.intent_router.route_with_permission_check(message, user_id, db)
                logger.info(f"识别意图: {intent}, 有权限: {has_permission}")
                
                # 如果没有权限，作为思考信息传递给AI而不是直接返回错误
                if not has_permission:
                    logger.info(f"用户 {user_id} 无权限访问: {intent}")
                    permission_info = f"[权限提示: {permission_msg}]" if permission_msg else "[权限提示: 您没有权限访问此功能]"
                    # 将权限信息作为思考过程发送给客户端
                    yield {"type": "thinking", "content": permission_info}
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
                # 如果有权限限制信息，将其添加到输入中供AI参考
                full_input = context + f"{permission_info}当前问题: {message}"
                
                # 第一步: 使用Agent获取信息和思考
                logger.info("Agent开始处理...")
                agent_response = await self.agent_executor.ainvoke({"input": full_input})
                agent_result = agent_response.get("output", "无法获取结果")
                
                # 提取中间步骤（工具调用）
                intermediate_steps = agent_response.get("intermediate_steps", [])
                
                # 构建完整的思考过程（不再单独输出工具调用）
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
            yield {"type": "error", "content": f"流式聊天服务异常: {str(e)}"}


@lru_cache()
def get_doubao_service(
    ai_history_mapper: AiHistoryMapper = Depends(get_ai_history_mapper),
    user_mapper: UserMapper = Depends(get_user_mapper)
) -> DoubaoService:
    return DoubaoService(ai_history_mapper, user_mapper)

from functools import lru_cache
from typing import AsyncGenerator, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_classic.agents import AgentExecutor, create_react_agent
from fastapi import Depends
from sqlmodel import Session
from api.mapper import (
    AiHistoryMapper, 
    get_ai_history_mapper, 
    UserMapper, 
    get_user_mapper
)
from .baseAIService import (
    BaseAiService, 
    get_agent_prompt, 
    initialize_ai_tools
)
from common.agent import IntentRouter, UserPermissionManager
from common.utils import fileLogger as logger
from config import load_config, load_secret_config

class GeminiService(BaseAiService):
    """Gemini AI Service"""
    
    
    def __init__(
            self, 
            ai_history_mapper: AiHistoryMapper = None, 
            user_mapper: Optional[UserMapper] = None
        ):
        super().__init__(ai_history_mapper, service_name="Gemini")
        
        # 初始化权限管理器
        self.perm_manager = UserPermissionManager(user_mapper)
        
        # 初始化Gemini客户端（使用第三方代理）
        try:
            gemini_cfg = load_config("gemini") or {}
            gemini_secret = load_secret_config("gemini") or {}
            self._api_key: str = gemini_secret.get("api_key")
            self._model_name: str = gemini_cfg.get("model_name", "gemini-2.0-flash")
            self._base_url: str = gemini_cfg.get("base_url", "https://api.openai-proxy.org/google")
            self._timeout: int = gemini_cfg.get("timeout", 30)
            
            if self._api_key:
                # 使用 ChatOpenAI 调用第三方代理的 Gemini API
                self.llm = ChatOpenAI(
                    model=self._model_name,
                    api_key=self._api_key,
                    base_url=self._base_url,
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
                    
                    logger.info("Gemini Agent服务初始化完成")
                except Exception as tool_error:
                    logger.warning(f"工具初始化部分失败: {tool_error}, 降级为基础对话模式")
                    self.agent_executor = None
                    self.intent_router = None
            else:
                self.llm = None
                self.agent_executor = None
                self.intent_router = None
                logger.warning("Gemini配置不完整，客户端未初始化")
        except Exception as e:
            self.llm = None
            self.agent_executor = None
            self.intent_router = None
            logger.error(f"初始化Gemini客户端失败: {e}")
    
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
            logger.info(f"Gemini 基础回复长度: {len(result)} 字符")
            return result
                
        except Exception as e:
            logger.error(f"Gemini 基础对话异常: {str(e)}")
            return f"对话服务异常: {str(e)}"

    async def with_reference_chat(self, message: str, reference_content: str) -> str:
        """
        基于参考文本的对话接口 - 使用权威参考文本进行评论和打分
        
        Args:
            message: 用户的消息或要评价的文章内容
            reference_content: 权威参考文本内容
            
        Returns:
            评价和打分结果
        """
        try:
            logger.info(f"基于参考文本的对话（长度: {len(reference_content)}）")
            
            if not getattr(self, 'llm', None):
                return "聊天服务未配置或初始化失败"
            
            # 使用基类的提示词方法
            prompt = self._get_reference_evaluation_prompt(message, reference_content)
            
            # 使用 LangChain 调用
            messages = [
                SystemMessage(content="你是一个专业的文章评价助手。请根据提供的权威参考文本进行客观、专业的评价。"),
                HumanMessage(content=prompt)
            ]
            
            response = await self.llm.ainvoke(messages)
            result: str = response.content
            logger.info(f"Gemini 参考文本对话回复长度: {len(result)} 字符")
            return result
            
        except Exception as e:
            logger.error(f"Gemini参考文本对话异常: {str(e)}")
            return f"对话服务异常: {str(e)}"

    async def summarize_content(self, content: str, max_length: int = 1000) -> str:
        """
        使用Gemini大模型对提取的内容进行总结
        
        Args:
            content: 需要总结的内容
            max_length: 总结后的最大长度
            
        Returns:
            总结后的内容
        """
        try:
            logger.info(f"Gemini开始总结内容，原始长度: {len(content)} 字符")
            
            if not getattr(self, 'llm', None):
                return "总结服务未配置或初始化失败"
            
            # 使用基类的提示词方法
            prompt = self._get_summarize_prompt(content, max_length)
            
            messages = [
                SystemMessage(content="你是一个专业的内容总结助手。请精准提取核心信息，用凝练的语言进行总结。"),
                HumanMessage(content=prompt)
            ]
            
            response = await self.llm.ainvoke(messages)
            result: str = response.content[:max_length]
            logger.info(f"Gemini内容总结完成，总结长度: {len(result)} 字符")
            return result
            
        except Exception as e:
            logger.error(f"Gemini内容总结异常: {str(e)}")
            return f"总结服务异常: {str(e)}"

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
                intent, has_permission, permission_msg = self.intent_router.route_with_permission_check(message, user_id, db)
                logger.info(f"识别意图: {intent}, 有权限: {has_permission}")
                
                # 如果没有权限，直接返回权限提示信息
                if not has_permission:
                    logger.info(f"用户 {user_id} 无权限访问: {intent}")
                    return permission_msg or "您没有权限访问此功能，请联系管理员开通相关权限。"
                    
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
            
            logger.info(f"Gemini回复长度: {len(result)} 字符")
            return result
                
        except Exception as e:
            logger.error(f"Gemini聊天异常: {str(e)}")
            if "API_KEY_INVALID" in str(e) or "invalid API key" in str(e):
                return "API密钥无效。请检查Gemini API密钥配置。"
            elif "QUOTA_EXCEEDED" in str(e):
                return "API配额已超限。请稍后重试或检查配额设置。"
            elif "RATE_LIMIT_EXCEEDED" in str(e):
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
                
                try:
                    async for chunk in self.llm.astream(messages):
                        try:
                            if chunk.content:
                                logger.debug(f"收到流式内容块，长度: {len(chunk.content)} 字符")
                                yield {"type": "content", "content": chunk.content}
                        except Exception as chunk_error:
                            logger.error(f"处理流式内容块异常: {str(chunk_error)}")
                            continue
                except Exception as stream_error:
                    error_msg = str(stream_error)
                    logger.error(f"基础流式对话失败: {error_msg}")
                    
                    # 检测配额和限流错误，作为普通内容返回
                    if "ResourceExhausted" in error_msg or "429" in error_msg:
                        if "quota" in error_msg.lower():
                            yield {"type": "content", "content": "😔 Gemini API 配额已用完。建议切换到豆包或通义千问服务。"}
                        else:
                            yield {"type": "content", "content": "😔 Gemini API 请求频率超限。请稍后再试。"}
                    elif "invalid" in error_msg.lower() and "key" in error_msg.lower():
                        yield {"type": "content", "content": "❌ API 密钥无效。"}
                    else:
                        yield {"type": "content", "content": f"❌ 服务异常: {error_msg[:100]}"}
                return
            
            # 1. 权限检查（如果有用户ID和数据库会话）
            intent = "general_chat"
            permission_info = ""
            if self.intent_router and db and user_id:
                intent, has_permission, permission_msg = self.intent_router.route_with_permission_check(message, user_id, db)
                logger.info(f"识别意图: {intent}, 有权限: {has_permission}")
                
                # 如果没有权限，直接流式输出权限提示信息并返回
                if not has_permission:
                    logger.info(f"用户 {user_id} 无权限访问: {intent}")
                    permission_message = permission_msg or "您没有权限访问此功能，请联系管理员开通相关权限。"
                    
                    # 发送思考过程（说明为什么没有权限）
                    thinking = f"检测到用户请求需要 {intent} 权限，但当前用户权限不足。"
                    yield {"type": "thinking", "content": thinking}
                    
                    # 流式输出友好的权限提示信息
                    for char in permission_message:
                        yield {"type": "content", "content": char}
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
                
                try:
                    async for chunk in self.llm.astream(messages):
                        try:
                            if chunk.content:
                                yield {"type": "content", "content": chunk.content}
                        except Exception as chunk_error:
                            logger.error(f"处理流式内容块异常: {str(chunk_error)}")
                            continue
                except Exception as stream_error:
                    error_msg = str(stream_error)
                    logger.error(f"流式聊天失败: {error_msg}")
                    
                    # 检测配额和限流错误，作为普通内容返回
                    if "ResourceExhausted" in error_msg or "429" in error_msg:
                        if "quota" in error_msg.lower():
                            yield {"type": "content", "content": "😔 Gemini API 配额已用完。建议切换到豆包或通义千问服务。"}
                        else:
                            yield {"type": "content", "content": "😔 Gemini API 请求频率超限。请稍后再试。"}
                    elif "invalid" in error_msg.lower() and "key" in error_msg.lower():
                        yield {"type": "content", "content": "❌ API 密钥无效。"}
                    else:
                        yield {"type": "content", "content": f"❌ 服务异常: {error_msg[:100]}"}
                
            else:
                # 使用Agent处理获取信息,然后流式输出最终答案
                logger.info("使用Agent处理,可同时调用SQL和RAG工具")
                
                # 添加历史上下文到输入
                context = self._build_chat_context(chat_history)
                full_input = context + f"当前问题: {message}"
                
                # 第一步: 使用Agent获取信息和思考
                logger.info("Agent开始处理...")
                try:
                    agent_response = await self.agent_executor.ainvoke({"input": full_input})
                    agent_result = agent_response.get("output", "无法获取结果")
                except Exception as agent_error:
                    error_msg = str(agent_error)
                    logger.error(f"Agent执行失败: {error_msg}")
                    
                    # 检测配额和限流错误并直接返回，作为普通内容
                    if "ResourceExhausted" in error_msg or "429" in error_msg:
                        if "quota" in error_msg.lower():
                            yield {"type": "content", "content": "😔 Gemini API 配额已用完。建议切换到豆包或通义千问服务。"}
                        else:
                            yield {"type": "content", "content": "😔 Gemini API 请求频率超限。请稍后再试或切换其他服务。"}
                    elif "API_KEY_INVALID" in error_msg or "invalid API key" in error_msg.lower():
                        yield {"type": "content", "content": "❌ API 密钥无效。"}
                    else:
                        yield {"type": "content", "content": f"❌ AI 处理失败: {error_msg[:100]}"}
                    return
                
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
                
                try:
                    async for chunk in self.llm.astream(stream_messages):
                        try:
                            if chunk.content:
                                yield {"type": "content", "content": chunk.content}
                        except Exception as chunk_error:
                            logger.error(f"处理流式内容块异常: {str(chunk_error)}")
                            continue
                except Exception as final_stream_error:
                    error_msg = str(final_stream_error)
                    logger.error(f"最终流式输出失败: {error_msg}")
                    
                    # 检测配额和限流错误，作为普通内容返回
                    if "ResourceExhausted" in error_msg or "429" in error_msg:
                        if "quota" in error_msg.lower():
                            yield {"type": "content", "content": "😔 Gemini API 配额已用完。建议切换到豆包或通义千问服务。"}
                        else:
                            yield {"type": "content", "content": "😔 Gemini API 请求频率超限。请稍后再试。"}
                    elif "invalid" in error_msg.lower() and "key" in error_msg.lower():
                        yield {"type": "content", "content": "❌ API 密钥无效。"}
                    else:
                        yield {"type": "content", "content": f"❌ 输出异常: {error_msg[:100]}"}
                    
        except Exception as e:
            error_msg = str(e)
            logger.error(f"流式聊天异常: {error_msg}")
            
            # 检测配额和限流错误，作为普通内容返回
            if "ResourceExhausted" in error_msg or "429" in error_msg:
                if "quota" in error_msg.lower():
                    yield {"type": "content", "content": "😔 Gemini API 配额已用完。请稍后再试或切换到其他 AI 服务（豆包/通义千问）。"}
                else:
                    yield {"type": "content", "content": "😔 Gemini API 请求过于频繁，已达到速率限制。请稍后再试。"}
            elif "API_KEY_INVALID" in error_msg or "invalid API key" in error_msg.lower():
                yield {"type": "content", "content": "❌ API 密钥无效。请检查 Gemini API 密钥配置。"}
            elif "403" in error_msg or "permission" in error_msg.lower():
                yield {"type": "content", "content": "❌ API 权限不足。请检查 API 密钥权限。"}
            elif "timeout" in error_msg.lower():
                yield {"type": "content", "content": "⏱️ 请求超时。请稍后重试。"}
            else:
                yield {"type": "content", "content": f"❌ 服务异常: {error_msg[:200]}"}

@lru_cache()
def get_gemini_service(
    ai_history_mapper: AiHistoryMapper = Depends(get_ai_history_mapper),
    user_mapper: UserMapper = Depends(get_user_mapper)
) -> GeminiService:
    """获取Gemini服务单例实例"""
    return GeminiService(
            ai_history_mapper, 
            user_mapper
        )

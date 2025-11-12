from functools import lru_cache
from typing import AsyncGenerator, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from fastapi import Depends
from sqlmodel import Session
from api.service import PromptService, get_prompt_service
from common.utils import fileLogger as logger
from config import load_config, load_secret_config

class TongyiService:
    def __init__(self, promptService: PromptService):
        self.promptService = promptService
        # 把通义千问客户端的配置和初始化放到实例内，避免模块导入时执行网络初始化
        try:
            tongyi_cfg = load_config("tongyi") or {}
            tongyi_secret = load_secret_config("tongyi") or {}
            self._api_key: str = tongyi_secret.get("api_key")
            self._model_name: str = tongyi_cfg.get("model_name", "qwen-flash")
            self._base_url: str = tongyi_cfg.get("base_url", "https://dashscope.aliyuncs.com/compatible-mode/v1")
            self._timeout: int = tongyi_cfg.get("timeout", 30)
            
            if self._api_key:
                self.tongyi_client = ChatOpenAI(
                    model=self._model_name,
                    openai_api_key=self._api_key,
                    openai_api_base=self._base_url,
                    temperature=0.7,
                    timeout=self._timeout,
                )
                logger.info("通义千问服务初始化完成 (LangChain)")
            else:
                self.tongyi_client = None
                logger.warning("通义千问配置不完整，客户端未初始化")
        except Exception as e:
            self.tongyi_client = None
            logger.error(f"初始化通义千问客户端失败: {e}")

    async def basic_chat(self, message: str) -> str:
        """最基础的对话接口 - 不使用知识库和向量数据库"""
        try:
            logger.info(f"基础对话: {message}")
            
            if not getattr(self, 'tongyi_client', None):
                return "聊天服务未配置或初始化失败"
            
            # 使用 LangChain 调用
            messages = [
                SystemMessage(content="你是一个中文AI助手，用于提供文章和博客推荐及分析系统数据。"),
                HumanMessage(content=message)
            ]
            response = await self.tongyi_client.ainvoke(messages)
            
            content: str = response.content
            logger.info(f"通义千问基础回复长度: {len(content)} 字符")
            return content
                
        except Exception as e:
            logger.error(f"通义千问基础对话异常: {str(e)}")
            return f"对话服务异常: {str(e)}"

    async def simple_chat(self, message: str, user_id: str = "default", db: Optional[Session] = None) -> str:
        """简单聊天接口"""
        try:
            prompt: str = self.promptService.get_prompt(message, db)
            logger.info(f"用户 {user_id} 发送消息: {prompt}")
            
            if not getattr(self, 'tongyi_client', None):
                return "聊天服务未配置或初始化失败"
            
            # 使用 LangChain 调用
            messages = [
                SystemMessage(content="你是一个中文AI助手，用于提供文章和博客推荐及分析系统数据。"),
                HumanMessage(content=prompt)
            ]
            response = await self.tongyi_client.ainvoke(messages)
            
            content: str = response.content
            logger.info(f"通义千问回复长度: {len(content)} 字符")
            return content
                
        except Exception as e:
            logger.error(f"通义千问聊天异常: {str(e)}")
            if "invalid" in str(e).lower() and "key" in str(e).lower():
                return "API密钥无效。请检查通义千问API密钥配置。"
            elif "quota" in str(e).lower() or "exceeded" in str(e).lower():
                return "API配额已超限。请稍后重试或检查配额设置。"
            elif "rate" in str(e).lower() and "limit" in str(e).lower():
                return "API调用频率超限。请稍后重试。"
            return f"聊天服务异常: {str(e)}"
        
    async def stream_chat(self, message: str, user_id: str = "default", db: Optional[Session] = None) -> AsyncGenerator[str, None]:
        """流式聊天接口 - 兼容异步调用"""
        try:
            prompt: str = self.promptService.get_prompt(message, db)
            logger.info(f"用户 {user_id} 开始流式聊天: {prompt}")
            
            if not getattr(self, 'tongyi_client', None):
                yield "聊天服务未配置或初始化失败"
                return
            
            # 使用 LangChain 流式调用
            messages = [
                SystemMessage(content="你是一个中文AI助手，用于提供文章和博客推荐及分析系统数据。"),
                HumanMessage(content=prompt)
            ]
            
            full_text = ""
            async for chunk in self.tongyi_client.astream(messages):
                try:
                    if chunk.content:
                        content_piece = chunk.content
                        logger.debug(f"收到流式内容块，长度: {len(content_piece)} 字符")
                        full_text += content_piece
                        yield content_piece
                except Exception as chunk_error:
                    logger.error(f"处理流式内容块异常: {str(chunk_error)}")
                    continue
            
            if full_text:
                logger.info(f"通义千问流式回复总长度: {len(full_text)} 字符")
                    
        except Exception as e:
            logger.error(f"流式聊天异常: {str(e)}")
            if "invalid" in str(e).lower() and "key" in str(e).lower():
                yield "API密钥无效。请检查通义千问API密钥配置。"
            elif "quota" in str(e).lower() or "exceeded" in str(e).lower():
                yield "API配额已超限。请稍后重试或检查配额设置。"
            elif "rate" in str(e).lower() and "limit" in str(e).lower():
                yield "API调用频率超限。请稍后重试。"
            else:
                yield f"流式聊天服务异常: {str(e)}"


@lru_cache()
def get_tongyi_service(promptService: PromptService = Depends(get_prompt_service)) -> TongyiService:
    """获取通义千问服务单例实例"""
    return TongyiService(promptService)

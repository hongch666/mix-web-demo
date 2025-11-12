from functools import lru_cache
from typing import AsyncGenerator, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from fastapi import Depends
from sqlmodel import Session
from api.service import PromptService, get_prompt_service
from common.utils import fileLogger as logger
from config import load_config, load_secret_config


class DoubaoService:
    def __init__(self, promptService: PromptService):
        self.promptService = promptService
        # 把豆包客户端的配置和初始化放到实例内，避免模块导入时执行网络初始化
        try:
            doubao_cfg = load_config("doubao") or {}
            doubao_secret = load_secret_config("doubao") or {}
            self._api_key: str = doubao_secret.get("api_key")
            self._model: str = doubao_cfg.get("model")
            self._base_url: str = doubao_cfg.get("base_url")
            self._timeout: int = doubao_cfg.get("timeout", 60)
            
            if self._api_key and self._base_url:
                self.doubao_client = ChatOpenAI(
                    model=self._model,
                    openai_api_key=self._api_key,
                    openai_api_base=self._base_url,
                    temperature=0.7,
                    timeout=self._timeout,
                )
                logger.info("豆包服务初始化完成 (LangChain)")
            else:
                self.doubao_client = None
                logger.warning("豆包配置不完整，客户端未初始化")
        except Exception as e:
            self.doubao_client = None
            logger.error(f"初始化豆包客户端失败: {e}")

    async def basic_chat(self, message: str) -> str:
        """最基础的对话接口 - 不使用知识库和向量数据库"""
        try:
            logger.info(f"基础对话: {message}")
            
            if not getattr(self, 'doubao_client', None):
                return "聊天服务未配置或初始化失败"
            
            # 使用 LangChain 调用
            messages = [
                SystemMessage(content="你是一个中文AI助手，用于提供文章和博客推荐及分析系统数据。"),
                HumanMessage(content=message)
            ]
            
            response = await self.doubao_client.ainvoke(messages)
            result: str = response.content
            logger.info(f"豆包基础回复长度: {len(result)} 字符")
            return result
            
        except Exception as e:
            logger.error(f"豆包基础对话异常: {str(e)}")
            return f"对话服务异常: {str(e)}"

    async def simple_chat(self, message: str, user_id: str = "default", db: Optional[Session] = None) -> str:
        """简单聊天接口"""
        try:
            prompt: str = self.promptService.get_prompt(message, db)
            logger.info(f"用户 {user_id} 发送消息: {prompt}")
            
            if not getattr(self, 'doubao_client', None):
                return "聊天服务未配置或初始化失败"
            
            # 使用 LangChain 调用
            messages = [
                SystemMessage(content="你是一个中文AI助手，用于提供文章和博客推荐及分析系统数据。"),
                HumanMessage(content=prompt)
            ]
            
            response = await self.doubao_client.ainvoke(messages)
            result: str = response.content
            logger.info(f"豆包回复长度: {len(result)} 字符")
            return result
            
        except Exception as e:
            logger.error(f"豆包聊天异常: {str(e)}")
            return f"聊天服务异常: {str(e)}"
        
    async def stream_chat(self, message: str, user_id: str = "default", db: Optional[Session] = None) -> AsyncGenerator[str, None]:
        """流式聊天接口 - 兼容异步调用"""
        try:
            logger.info(f"用户 {user_id} 开始流式聊天: {message}")

            prompt: str = self.promptService.get_prompt(message, db)
            logger.info(f"用户 {user_id} 发送消息: {prompt}")
            
            if not getattr(self, 'doubao_client', None):
                yield "聊天服务未配置或初始化失败"
                return
            
            # 使用 LangChain 流式调用
            messages = [
                SystemMessage(content="你是一个中文AI助手，用于提供文章和博客推荐及分析系统数据。"),
                HumanMessage(content=prompt)
            ]

            async for chunk in self.doubao_client.astream(messages):
                if chunk.content:
                    logger.debug(f"收到流式内容: {chunk.content}")
                    yield chunk.content
                    
        except Exception as e:
            logger.error(f"流式聊天异常: {str(e)}")
            yield f"流式聊天服务异常: {str(e)}"


@lru_cache()
def get_doubao_service(promptService: PromptService = Depends(get_prompt_service)) -> DoubaoService:
    return DoubaoService(promptService)

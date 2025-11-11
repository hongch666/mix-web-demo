import asyncio
from functools import lru_cache
from typing import Any, AsyncGenerator, Optional
from openai import OpenAI
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
            self._model: str = doubao_cfg.get("model")  # 修正：使用 model 而不是 model_name
            self._base_url: str = doubao_cfg.get("base_url")
            self._timeout: int = doubao_cfg.get("timeout", 60)
            
            if self._api_key and self._base_url:
                self.doubao_client: OpenAI = OpenAI(
                    base_url=self._base_url,
                    api_key=self._api_key,
                )
                logger.info("豆包服务初始化完成 (实例化)")
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
            
            # 使用豆包的 OpenAI 兼容接口
            completion = self.doubao_client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": "你是人工智能助手"},
                    {"role": "user", "content": message}
                ],
            )
            
            response: str = completion.choices[0].message.content
            logger.info(f"豆包基础回复长度: {len(response)} 字符")
            return response
            
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
            
            # 使用豆包的 OpenAI 兼容接口
            completion = self.doubao_client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": "你是人工智能助手"},
                    {"role": "user", "content": prompt}
                ],
            )
            
            response: str = completion.choices[0].message.content
            logger.info(f"豆包回复长度: {len(response)} 字符")
            return response
            
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
            
            # 使用豆包的流式接口
            def sync_stream() -> Any:
                return self.doubao_client.chat.completions.create(
                    model=self._model,
                    messages=[
                        {"role": "system", "content": "你是人工智能助手"},
                        {"role": "user", "content": prompt}
                    ],
                    stream=True,
                )

            loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()
            stream = await loop.run_in_executor(None, sync_stream)

            for chunk in stream:
                if not chunk.choices:
                    continue
                    
                content = chunk.choices[0].delta.content
                if content is not None:
                    logger.debug(f"收到流式内容: {content}")
                    yield content
                    
        except Exception as e:
            logger.error(f"流式聊天异常: {str(e)}")
            yield f"流式聊天服务异常: {str(e)}"


@lru_cache()
def get_doubao_service(promptService: PromptService = Depends(get_prompt_service)) -> DoubaoService:
    return DoubaoService(promptService)

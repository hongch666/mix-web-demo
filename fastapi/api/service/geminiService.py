import asyncio
from functools import lru_cache
from typing import Any, AsyncGenerator, Optional
import google.generativeai as genai
from fastapi import Depends
from sqlmodel import Session
from api.service import PromptService, get_prompt_service
from common.utils import fileLogger as logger
from config import load_config, load_secret_config


class GeminiService:
    def __init__(self,promptService: PromptService):
        self.promptService = promptService
        # 把 Gemini 客户端的配置和初始化放到实例内，避免模块导入时执行网络初始化
        try:
            gemini_cfg = load_config("gemini") or {}
            gemini_secret = load_secret_config("gemini") or {}
            self._api_key: str = gemini_secret.get("api_key")
            self._model_name: str = gemini_cfg.get("model_name", "gemini-1.5-flash")
            self._timeout: int = gemini_cfg.get("timeout", 30)
            
            if self._api_key:
                genai.configure(api_key=self._api_key)
                self.gemini_model = genai.GenerativeModel(self._model_name)
                logger.info("Gemini 服务初始化完成 (实例化)")
            else:
                self.gemini_model = None
                logger.warning("Gemini 配置不完整，客户端未初始化")
        except Exception as e:
            self.gemini_model = None
            logger.error(f"初始化 Gemini 客户端失败: {e}")

    async def basic_chat(self, message: str) -> str:
        """最基础的对话接口 - 不使用知识库和向量数据库"""
        try:
            logger.info(f"基础对话: {message}")
            
            if not getattr(self, 'gemini_model', None):
                return "聊天服务未配置或初始化失败"
            
            # 使用 run_in_executor 在线程池中运行同步的 Gemini API 调用
            loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                self.gemini_model.generate_content,
                message
            )
            
            if response and hasattr(response, 'text'):
                result: str = response.text
                logger.info(f"Gemini 基础回复长度: {len(result)} 字符")
                return result
            else:
                logger.warning("Gemini 没有返回有效内容")
                return "抱歉，没有收到回复"
                
        except Exception as e:
            logger.error(f"Gemini 基础对话异常: {str(e)}")
            return f"对话服务异常: {str(e)}"

    async def simple_chat(self,message: str, user_id: str = "default", db: Optional[Session] = None) -> str:
        """简单聊天接口"""
        try:
            prompt: str = self.promptService.get_prompt(message, db)
            logger.info(f"用户 {user_id} 发送消息: {prompt}")
            
            if not getattr(self, 'gemini_model', None):
                return "聊天服务未配置或初始化失败"
            
            # 使用 run_in_executor 在线程池中运行同步的 Gemini API 调用
            loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                self.gemini_model.generate_content,
                prompt
            )
            
            if response and hasattr(response, 'text'):
                result: str = response.text
                logger.info(f"Gemini 回复长度: {len(result)} 字符")
                return result
            else:
                logger.warning("Gemini 没有返回有效内容")
                return "抱歉，没有收到回复"
                
        except Exception as e:
            logger.error(f"Gemini 聊天异常: {str(e)}")
            if "API_KEY_INVALID" in str(e) or "invalid API key" in str(e):
                return "API密钥无效。请检查Gemini API密钥配置。"
            elif "QUOTA_EXCEEDED" in str(e):
                return "API配额已超限。请稍后重试或检查配额设置。"
            elif "RATE_LIMIT_EXCEEDED" in str(e):
                return "API调用频率超限。请稍后重试。"
            return f"聊天服务异常: {str(e)}"
        
    async def stream_chat(self,message: str, user_id: str = "default", db: Optional[Session] = None) -> AsyncGenerator[str, None]:
        """流式聊天接口 - 兼容异步调用"""
        try:
            prompt: str = self.promptService.get_prompt(message, db)
            logger.info(f"用户 {user_id} 开始流式聊天: {prompt}")
            
            if not getattr(self, 'gemini_model', None):
                yield "聊天服务未配置或初始化失败"
                return
            
            def sync_stream() -> Any:
                return self.gemini_model.generate_content(prompt, stream=True)

            loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()
            response_stream = await loop.run_in_executor(None, sync_stream)
            
            for chunk in response_stream:
                try:
                    if chunk and hasattr(chunk, 'text'):
                        content: str = chunk.text
                        if content:
                            logger.info(f"收到流式内容块，长度: {len(content)} 字符")
                            yield content
                    else:
                        logger.warning("收到空的流式内容块")
                except Exception as chunk_error:
                    logger.error(f"处理流式内容块异常: {str(chunk_error)}")
                    continue
                    
        except Exception as e:
            logger.error(f"流式聊天异常: {str(e)}")
            if "API_KEY_INVALID" in str(e) or "invalid API key" in str(e):
                yield "API密钥无效。请检查Gemini API密钥配置。"
            elif "QUOTA_EXCEEDED" in str(e):
                yield "API配额已超限。请稍后重试或检查配额设置。"
            elif "RATE_LIMIT_EXCEEDED" in str(e):
                yield "API调用频率超限。请稍后重试。"
            else:
                yield f"流式聊天服务异常: {str(e)}"

@lru_cache()
def get_gemini_service(promptService: PromptService = Depends(get_prompt_service)) -> GeminiService:
    """获取Gemini服务单例实例"""
    return GeminiService(promptService)
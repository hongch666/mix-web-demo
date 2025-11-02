import asyncio
import json
from functools import lru_cache
from typing import Any, AsyncGenerator, Optional
from openai import OpenAI
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
                self.tongyi_client = OpenAI(
                    api_key=self._api_key,
                    base_url=self._base_url,
                    timeout=self._timeout
                )
                logger.info("通义千问服务初始化完成 (实例化)")
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
            
            # 使用 run_in_executor 在线程池中运行同步的通义千问 API 调用
            loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()
            
            def sync_chat():
                return self.tongyi_client.chat.completions.create(
                    model=self._model_name,
                    messages=[
                        {"role": "user", "content": message}
                    ]
                )
            
            completion = await loop.run_in_executor(None, sync_chat)
            
            # 解析响应内容
            raw = completion.model_dump_json()
            if isinstance(raw, str):
                try:
                    data = json.loads(raw)
                except json.JSONDecodeError:
                    data = {}
            else:
                data = raw

            content = None
            try:
                content = data.get("choices", [])[0].get("message", {}).get("content")
            except Exception:
                try:
                    content = data["choices"][0]["message"]["content"]
                except Exception:
                    content = None
            
            if content:
                logger.info(f"通义千问基础回复长度: {len(content)} 字符")
                return content
            else:
                logger.warning("通义千问没有返回有效内容")
                return "抱歉，没有收到回复"
                
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
            
            # 使用 run_in_executor 在线程池中运行同步的通义千问 API 调用
            loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()
            
            def sync_chat():
                return self.tongyi_client.chat.completions.create(
                    model=self._model_name,
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": prompt}
                    ]
                )
            
            completion = await loop.run_in_executor(None, sync_chat)
            
            # 解析响应内容
            raw = completion.model_dump_json()
            if isinstance(raw, str):
                try:
                    data = json.loads(raw)
                except json.JSONDecodeError:
                    data = {}
            else:
                data = raw

            content = None
            try:
                content = data.get("choices", [])[0].get("message", {}).get("content")
            except Exception:
                try:
                    content = data["choices"][0]["message"]["content"]
                except Exception:
                    content = None
            
            if content:
                logger.info(f"通义千问回复长度: {len(content)} 字符")
                return content
            else:
                logger.warning("通义千问没有返回有效内容")
                return "抱歉，没有收到回复"
                
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
            
            def sync_stream() -> Any:
                return self.tongyi_client.chat.completions.create(
                    model=self._model_name,
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": prompt}
                    ],
                    stream=True,
                    stream_options={"include_usage": True}
                )

            loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()
            completion_stream = await loop.run_in_executor(None, sync_stream)
            
            full_text = ""
            for chunk in completion_stream:
                try:
                    raw = chunk.model_dump_json()
                    if isinstance(raw, str):
                        try:
                            data = json.loads(raw)
                        except json.JSONDecodeError:
                            data = {}
                    else:
                        data = raw or {}

                    # 尝试从多个位置获取内容
                    content_piece = None
                    choices = data.get("choices", []) if isinstance(data, dict) else []
                    if choices:
                        first = choices[0] if isinstance(choices[0], dict) else {}
                        # 流式模式: delta.content
                        delta = first.get("delta", {}) if isinstance(first, dict) else {}
                        content_piece = delta.get("content")
                        # 后备方案: message.content
                        if content_piece is None:
                            msg = first.get("message", {}) if isinstance(first, dict) else {}
                            content_piece = msg.get("content")

                    # 输出并累积流式内容片段
                    if content_piece:
                        logger.debug(f"收到流式内容块，长度: {len(content_piece)} 字符")
                        full_text += content_piece
                        yield content_piece
                    else:
                        # 仅包含使用统计的最终块
                        if not choices and data.get("usage"):
                            usage = data["usage"]
                            logger.info(f"通义千问流式响应完成，使用统计: {json.dumps(usage, ensure_ascii=False)}")
                            
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

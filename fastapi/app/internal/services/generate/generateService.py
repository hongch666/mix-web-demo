import asyncio
import re
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache, partial
from typing import Any, Optional, cast

import jieba.analyse

from app.core.base import Logger
from app.core.constants import AiUsers, HttpCode, Messages, Prompts
from app.core.errors import BusinessException
from app.internal.agents import get_reference_content_extractor
from app.internal.clients import SpringClient, get_spring_client

from ..llm.extend.claudeService import ClaudeService
from ..llm.extend.deepseekService import DeepseekService
from ..llm.extend.geminiService import GeminiService
from ..llm.extend.glmService import GlmService
from ..llm.extend.gptService import GptService
from ..llm.extend.qwenService import QwenService


@dataclass(frozen=True)
class AiCommentModel:
    """AI 评论模型登记项：服务名、评论用户 ID、降级文案与模型服务实例"""

    service_name: str
    user_id: int
    failed_text: str
    service: Any


class GenerateService:
    """生成 Service"""

    def __init__(
        self,
        glm_service: Optional[GlmService] = None,
        gemini_service: Optional[GeminiService] = None,
        gpt_service: Optional[GptService] = None,
        deepseek_service: Optional[DeepseekService] = None,
        claude_service: Optional[ClaudeService] = None,
        qwen_service: Optional[QwenService] = None,
        spring_client: Optional[SpringClient] = None,
    ) -> None:
        # 各模型服务允许缺省，调用失败由各调用点按异常兜底降级，因此按 Any 持有
        self.glm_service: Any = glm_service
        self.gpt_service: Any = gpt_service
        self.gemini_service: Any = gemini_service
        self.deepseek_service: Any = deepseek_service
        self.claude_service: Any = claude_service
        self.qwen_service: Any = qwen_service
        self._spring_client: SpringClient = spring_client or get_spring_client()

    async def extract_tags(self, text: str, topK: int = 5) -> list[str]:
        """
        提取文本中的关键词作为tags
        :param text: 文章内容
        :param topK: 返回关键词数量
        :return: 关键词列表
        """
        # 去除markdown格式符号
        text = re.sub(
            r"(```[\s\S]*?```|`[^`]*`|\!\[[^\]]*\]\([^\)]*\)|\[[^\]]*\]\([^\)]*\)|[#>*_~\-\+\=\[\]`]|\d+\.|\n)",
            " ",
            text,
        )
        text = re.sub(r"\s+", " ", text).strip()
        # jieba 未标注返回值，withWeight 默认 False 时实际是纯词表，这里按调用契约收窄
        tags: list[str] = cast(list[str], jieba.analyse.extract_tags(text, topK=topK))
        return tags

    @staticmethod
    def _build_comment_data(
        article_id: int, user_id: int, content: str, star: float
    ) -> dict[str, Any]:
        """构造Spring评论接口请求数据（Spring使用SNAKE_CASE反序列化，键名需下划线）"""
        now = datetime.now().isoformat()
        return {
            "article_id": article_id,
            "user_id": user_id,
            "content": content,
            "star": star,
            "create_time": now,
            "update_time": now,
        }

    def _ai_comment_models(self) -> tuple[AiCommentModel, ...]:
        """AI 评论模型登记项，新增模型只需在此登记，评论用户与降级文案随之生效"""
        return (
            AiCommentModel(
                "GLM", AiUsers.GLM_ID, Messages.GLM_CALL_FAILED_ERROR, self.glm_service
            ),
            AiCommentModel(
                "Gemini",
                AiUsers.GEMINI_ID,
                Messages.GEMINI_CALL_FAILED_ERROR,
                self.gemini_service,
            ),
            AiCommentModel(
                "GPT", AiUsers.GPT_ID, Messages.GPT_CALL_FAILED_ERROR, self.gpt_service
            ),
            AiCommentModel(
                "DeepSeek",
                AiUsers.DEEPSEEK_ID,
                Messages.DEEPSEEK_CALL_FAILED_ERROR,
                self.deepseek_service,
            ),
            AiCommentModel(
                "Claude",
                AiUsers.CLAUDE_ID,
                Messages.CLAUDE_CALL_FAILED_ERROR,
                self.claude_service,
            ),
            AiCommentModel(
                "Qwen",
                AiUsers.QWEN_ID,
                Messages.QWEN_CALL_FAILED_ERROR,
                self.qwen_service,
            ),
        )

    def _build_ai_comment(
        self,
        article_id: int,
        model: AiCommentModel,
        response: Any,
        failed_message: Callable[[str, Any], str] = Messages.LLM_FINAL_FAILED,
    ) -> dict[str, Any]:
        """解析模型返回并构建评论数据，异常响应降级为失败文案与默认分"""
        if isinstance(response, Exception):
            Logger.error(failed_message(model.service_name, response))
            response = model.failed_text
        content, star = self._parse_ai_comment_response(response)
        return self._build_comment_data(article_id, model.user_id, content, star)

    async def _call_models_for_comments(
        self, models: tuple[AiCommentModel, ...], prompt: str
    ) -> list[Any]:
        """并发调用各模型生成评论，单模型异常按返回值透传，由构建阶段降级"""

        async def call_model(model: AiCommentModel) -> Any:
            start = time.time()
            try:
                result = await model.service.basic_chat(prompt)
            except Exception as e:
                Logger.error(
                    Messages.LLM_CALL_FAILED_TIMED(
                        model.service_name, time.time() - start, e
                    )
                )
                return e
            Logger.info(
                Messages.LLM_CALL_COMPLETED(model.service_name, time.time() - start)
            )
            return result

        responses = await asyncio.gather(
            *(call_model(model) for model in models), return_exceptions=True
        )
        return list(responses)

    async def _call_models_with_reference(
        self,
        models: tuple[AiCommentModel, ...],
        article_content: str,
        reference_content: str,
    ) -> list[Any]:
        """并发调用各模型基于参考文本生成评论，单模型异常按返回值透传"""

        async def call_model(model: AiCommentModel) -> Any:
            start = time.time()
            try:
                result = await model.service.with_reference_chat(
                    article_content, reference_content
                )
            except Exception as e:
                Logger.error(
                    Messages.LLM_REFERENCE_CALL_FAILED_TIMED(
                        model.service_name, time.time() - start, e
                    )
                )
                return e
            Logger.info(
                Messages.LLM_REFERENCE_CALL_COMPLETED(
                    model.service_name, time.time() - start
                )
            )
            return result

        responses = await asyncio.gather(
            *(call_model(model) for model in models), return_exceptions=True
        )
        return list(responses)

    async def generate_ai_comments(self, article_id: int) -> None:

        # 1. 判断是否需要生成AI评论
        ai_comments_count = await self._spring_client.get_ai_comments_num_by_article_id(
            article_id
        )
        # 2. 获取文章信息（与删除AI评论并行，互不依赖）
        if ai_comments_count > 0:
            Logger.info(Messages.ARTICLE_AI_COMMENT_EXISTS_DELETING(article_id))
            _, articles = await asyncio.gather(
                self._spring_client.delete_ai_comments_by_article_id(article_id),
                self._spring_client.get_articles_by_ids([article_id]),
            )
        else:
            articles = await self._spring_client.get_articles_by_ids([article_id])
        if not articles:
            raise BusinessException(
                Messages.ARTICLE_NOT_EXISTS_ERROR,
                HttpCode.NOT_FOUND,
                Messages.ERROR_ARTICLE_NOT_FOUND,
            )
        article_data = articles[0]
        # 2.2 构建提示词
        prompt = Prompts.ARTICLE_EVALUATION(
            article_data.get("title", ""),
            article_data.get("tags", ""),
            article_data.get("content", ""),
        )
        # 2.3 异步并发调用所有大模型生成AI评论
        Logger.info(Messages.CONCURRENT_LLM_AI_COMMENT_START(article_id))
        models = self._ai_comment_models()

        # 记录整体开始时间
        total_start_time = time.time()
        responses = await self._call_models_for_comments(models, prompt)

        # 记录整体结束时间
        total_elapsed = time.time() - total_start_time
        Logger.info(Messages.CONCURRENT_LLM_ALL_COMPLETED(total_elapsed, article_id))

        # 3. 构建AI评论对象，异常返回由构建阶段替换为降级文案
        comments = [
            self._build_ai_comment(article_id, model, response)
            for model, response in zip(models, responses, strict=True)
        ]

        # 4. 保存AI评论到数据库（通过Spring远程调用并行插入，互不干扰）
        async def _insert_comment(comment: dict[str, Any]) -> None:
            await self._spring_client.create_comment(comment)

        await asyncio.gather(*(_insert_comment(comment) for comment in comments))
        Logger.info(Messages.AI_COMMENT_GENERATED_AND_SAVED(article_id))

    async def generate_ai_comments_in_background(self, article_id: int) -> None:
        """后台生成 AI 评论"""
        await self.generate_ai_comments(article_id)

    # 定义工具函数解析大模型返回结果
    def _parse_ai_comment_response(self, response: str) -> tuple[str, float]:
        content = ""
        star = 6.0
        # 提取评价内容
        content_match = re.search(
            r"评价内容[：:]\s*(.+?)(?=评分|$)", response, re.DOTALL
        )
        if content_match:
            content = content_match.group(1).strip()
        else:
            # 如果没有找到标记，使用整个响应的前200字
            lines = response.split("\n")
            for line in lines:
                if "评分" not in line and line.strip():
                    content += line.strip() + " "
            content = content[:200].strip()

        # 提取评分
        star_match = re.search(r"评分[：:]\s*(\d+(?:\.\d+)?)", response)
        if star_match:
            star = float(star_match.group(1))
        else:
            # 尝试查找任何数字后跟"分"的模式
            score_match = re.search(r"(\d+(?:\.\d+)?)\s*分", response)
            if score_match:
                star = float(score_match.group(1))

        if not content:
            content = response[:200]

        return content, star

    async def generate_ai_comments_with_reference(self, article_id: int) -> None:
        """
        基于权威参考文本生成AI评论
        获取文章的子分类权威参考文本，提取内容，然后调用AI服务进行评价

        Args:
            article_id: 文章ID
            db: 数据库会话
        """
        # 1. 判断是否需要生成AI评论
        ai_comments_count = await self._spring_client.get_ai_comments_num_by_article_id(
            article_id
        )
        # 2. 获取文章信息（与删除AI评论并行，互不依赖）
        if ai_comments_count > 0:
            Logger.info(Messages.ARTICLE_AI_COMMENT_EXISTS_DELETING(article_id))
            _, articles = await asyncio.gather(
                self._spring_client.delete_ai_comments_by_article_id(article_id),
                self._spring_client.get_articles_by_ids([article_id]),
            )
        else:
            articles = await self._spring_client.get_articles_by_ids([article_id])
        if not articles:
            Logger.error(Messages.ARTICLE_NOT_FOUND_WITH_ID(article_id))
            return
        article_data = articles[0]
        # 各模型的评论身份与降级文案在单次调用内固定
        models = self._ai_comment_models()

        Logger.info(Messages.REFERENCE_BASED_AI_COMMENT_START(article_id))

        # 3. 获取权威参考文本（通过SpringClient远程调用）
        reference_content = None

        # 获取文章的子分类ID
        sub_category_id = article_data.get("sub_category_id")

        if sub_category_id:
            category_ref = (
                await self._spring_client.get_category_reference_by_sub_category_id(
                    sub_category_id
                )
            )

            if category_ref:
                Logger.info(
                    Messages.REFERENCE_TEXT_TYPE_FOUND(str(category_ref.get("type")))
                )
                Logger.info(Messages.REFERENCE_TEXT_DETAIL(category_ref))

                # 4. 根据类型提取内容并使用大模型进行总结
                extractor = get_reference_content_extractor()
                ref_type = category_ref.get("type", "link")
                # 未知类型时保持空串，提取器对空值直接返回空内容
                ref_value: str = ""

                if ref_type == "pdf":
                    ref_value = str(category_ref.get("pdf") or "")
                    Logger.info(Messages.REFERENCE_PDF_EXTRACTION_START(ref_value))
                elif ref_type == "link":
                    ref_value = str(category_ref.get("link") or "")
                    Logger.info(Messages.REFERENCE_LINK_EXTRACTION_START(ref_value))

                # 定义各大模型的总结函数
                async def summarize_with(model: AiCommentModel, content: str) -> str:
                    try:
                        return await model.service.summarize_content(
                            content, max_length=1500
                        )
                    except Exception as e:
                        Logger.error(
                            Messages.LLM_SUMMARIZE_FAILED(model.service_name, e)
                        )
                        return content[:1500]

                # 并发调用各大模型对提取的内容进行总结
                summarize_tasks = [
                    extractor.extract_reference_content(
                        ref_type, ref_value, 3000, partial(summarize_with, model)
                    )
                    for model in models
                ]

                summary_results = await asyncio.gather(
                    *summarize_tasks, return_exceptions=True
                )

                # 合并各大模型的总结结果，非字符串结果不参与合并
                summaries = [
                    Messages.LLM_SUMMARY_RESULT_ENTRY(model.service_name, str(result))
                    for model, result in zip(models, summary_results, strict=True)
                    if isinstance(result, str) and result
                ]

                if summaries:
                    reference_content = "\n\n".join(summaries)
                    Logger.info(
                        Messages.REFERENCE_TEXT_EXTRACTED_AND_SUMMARIZED(
                            len(reference_content)
                        )
                    )
                else:
                    Logger.warning(
                        Messages.REFERENCE_TEXT_EXTRACTION_FAILED_TYPE(ref_type)
                    )
                    reference_content = Messages.REFERENCE_TEXT_FALLBACK_CONTENT(
                        ref_type, str(ref_value)
                    )
            else:
                Logger.info(Messages.SUB_CATEGORY_NO_REFERENCE(sub_category_id))
                reference_content = None
        else:
            Logger.warning(Messages.ARTICLE_NO_SUB_CATEGORY(article_id))
            reference_content = None
        # 如果没有参考文本，使用默认参考提示
        if not reference_content:
            reference_content = Messages.CATEGORY_NO_AUTHORITATIVE_REFERENCE_TEXT_ERROR

        # 5. 构建要评价的内容
        article_content = Prompts.ARTICLE_REFERENCE_CONTENT(
            article_data.get("title", ""),
            article_data.get("tags", ""),
            article_data.get("content", ""),
        )

        # 6. 异步并发调用所有大模型生成AI评论
        Logger.info(Messages.CONCURRENT_LLM_REFERENCE_AI_COMMENT_START(article_id))

        total_start_time = time.time()
        responses = await self._call_models_with_reference(
            models, article_content, reference_content
        )

        total_elapsed = time.time() - total_start_time
        Logger.info(
            Messages.CONCURRENT_LLM_REFERENCE_ALL_COMPLETED(total_elapsed, article_id)
        )

        # 7. 构建AI评论对象，异常返回由构建阶段替换为降级文案
        comments = [
            self._build_ai_comment(
                article_id, model, response, Messages.LLM_REFERENCE_FINAL_FAILED
            )
            for model, response in zip(models, responses, strict=True)
        ]

        # 8. 保存AI评论到数据库（通过Spring远程调用并行插入，互不干扰）
        async def _insert_comment_ref(comment: dict[str, Any]) -> None:
            await self._spring_client.create_comment(comment)

        await asyncio.gather(*(_insert_comment_ref(comment) for comment in comments))
        Logger.info(Messages.REFERENCE_AI_COMMENT_GENERATED_AND_SAVED(article_id))

    async def generate_authority_article_with_ai_summaries(
        self, reference_type: str, reference_value: str
    ) -> dict[str, Any]:
        """
        生成权威文章 - 使用三个大模型并发对提取的内容进行总结

        Args:
            reference_type: "link" 或 "pdf"
            reference_value: 对应的 URL 或路径

        Returns:
            包含三个大模型总结的字典
        """
        try:
            Logger.info(
                Messages.AUTHORITY_ARTICLE_GENERATION_START(
                    reference_type, reference_value
                )
            )

            # 1. 提取原始内容
            extractor = get_reference_content_extractor()

            if reference_type.lower() == "pdf":
                raw_content = await extractor.extract_pdf_content(
                    reference_value, max_length=3000
                )
            elif reference_type.lower() == "link":
                raw_content = await extractor.extract_link_content(
                    reference_value, max_length=3000
                )
            else:
                Logger.error(Messages.UNSUPPORTED_REFERENCE_TYPE(reference_type))
                return {
                    "status": "error",
                    "message": Messages.UNSUPPORTED_REFERENCE_TYPE(reference_type),
                }

            if not raw_content:
                Logger.warning(Messages.REFERENCE_TEXT_EXTRACTION_ERROR)
                return {
                    "status": "error",
                    "message": Messages.REFERENCE_TEXT_EXTRACTION_ERROR,
                }

            Logger.info(Messages.RAW_CONTENT_EXTRACTION_COMPLETED(len(raw_content)))

            # 2. 并发调用三个大模型进行总结
            Logger.info(Messages.CONCURRENT_SUMMARY_MESSAGE)
            total_start_time = time.time()

            async def timed_glm_summarize() -> Optional[str]:
                start = time.time()
                try:
                    result = await self.glm_service.summarize_content(
                        raw_content, max_length=1500
                    )
                    elapsed = time.time() - start
                    Logger.info(
                        Messages.LLM_SUMMARIZE_COMPLETED(
                            "GLM", elapsed, len(result) if result else 0
                        )
                    )
                    return result
                except Exception as e:
                    elapsed = time.time() - start
                    Logger.error(Messages.LLM_SUMMARIZE_FAILED_TIMED("GLM", elapsed, e))
                    return None

            async def timed_gemini_summarize() -> Optional[str]:
                start = time.time()
                try:
                    result = await self.gemini_service.summarize_content(
                        raw_content, max_length=1500
                    )
                    elapsed = time.time() - start
                    Logger.info(
                        Messages.LLM_SUMMARIZE_COMPLETED(
                            "Gemini", elapsed, len(result) if result else 0
                        )
                    )
                    return result
                except Exception as e:
                    elapsed = time.time() - start
                    Logger.error(
                        Messages.LLM_SUMMARIZE_FAILED_TIMED("Gemini", elapsed, e)
                    )
                    return None

            async def timed_gpt_summarize() -> Optional[str]:
                start = time.time()
                try:
                    result = await self.gpt_service.summarize_content(
                        raw_content, max_length=1500
                    )
                    elapsed = time.time() - start
                    Logger.info(
                        Messages.LLM_SUMMARIZE_COMPLETED(
                            "GPT", elapsed, len(result) if result else 0
                        )
                    )
                    return result
                except Exception as e:
                    elapsed = time.time() - start
                    Logger.error(Messages.LLM_SUMMARIZE_FAILED_TIMED("GPT", elapsed, e))
                    return None

            # 并发执行三个总结任务
            summaries = await asyncio.gather(
                timed_glm_summarize(),
                timed_gemini_summarize(),
                timed_gpt_summarize(),
                return_exceptions=False,
            )

            total_elapsed = time.time() - total_start_time
            Logger.info(Messages.ALL_CONCURRENT_SUMMARIZE_COMPLETED(total_elapsed))

            # 3. 构建返回结果
            result = {
                "status": "success",
                "reference_type": reference_type,
                "reference_value": reference_value,
                "raw_content_length": len(raw_content),
                "raw_content_preview": raw_content[:500] if raw_content else "",
                "summaries": {
                    "glm": {
                        "content": summaries[0],
                        "length": len(summaries[0]) if summaries[0] else 0,
                    },
                    "gemini": {
                        "content": summaries[1],
                        "length": len(summaries[1]) if summaries[1] else 0,
                    },
                    "gpt": {
                        "content": summaries[2],
                        "length": len(summaries[2]) if summaries[2] else 0,
                    },
                },
                "total_execution_time": total_elapsed,
            }

            Logger.info(Messages.CONCURRENT_CHAT_MESSAGE_SUCCESS)
            return result

        except Exception as e:
            Logger.error(Messages.AUTHORITY_ARTICLE_GENERATION_EXCEPTION(str(e)))
            return {
                "status": "error",
                "message": Messages.AUTHORITY_ARTICLE_GENERATION_FAILED(str(e)),
            }

    async def generate_ai_comments_with_reference_in_background(
        self, article_id: int
    ) -> None:
        """后台生成带参考文本的 AI 评论"""
        await self.generate_ai_comments_with_reference(article_id)


@lru_cache
def get_generate_service(
    glm_service: GlmService,
    gemini_service: GeminiService,
    gpt_service: GptService,
    deepseek_service: DeepseekService,
    claude_service: ClaudeService,
    qwen_service: QwenService,
    spring_client: SpringClient,
) -> GenerateService:
    return GenerateService(
        glm_service,
        gemini_service,
        gpt_service,
        deepseek_service,
        claude_service,
        qwen_service,
        spring_client,
    )

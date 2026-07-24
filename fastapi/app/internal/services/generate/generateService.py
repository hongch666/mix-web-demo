import asyncio
import re
import time
from datetime import datetime
from functools import lru_cache
from typing import Any, Dict, Optional

import jieba.analyse
from app.core.base import Logger
from app.core.constants import HttpCode, Messages, Prompts
from app.core.db import AsyncSessionLocal
from app.core.errors import BusinessException
from app.internal.agents import get_reference_content_extractor
from app.internal.crud import (
    ArticleMapper,
    CategoryReferenceMapper,
    CommentsMapper,
    get_article_mapper,
    get_category_reference_mapper,
    get_comments_mapper,
)
from app.internal.models import Comments

from fastapi import Depends

from ..llm.extend.deepseekService import DeepseekService, get_deepseek_service
from ..llm.extend.geminiService import GeminiService, get_gemini_service
from ..llm.extend.gptService import GptService, get_gpt_service


class GenerateService:
    """生成 Service"""

    def __init__(
        self,
        comments_mapper: Optional[CommentsMapper] = None,
        article_mapper: Optional[ArticleMapper] = None,
        deepseek_service: Optional[DeepseekService] = None,
        gemini_service: Optional[GeminiService] = None,
        gpt_service: Optional[GptService] = None,
    ) -> None:
        self.comments_mapper: Optional[CommentsMapper] = comments_mapper
        self.article_mapper: Optional[ArticleMapper] = article_mapper
        self.deepseek_service: Optional[DeepseekService] = deepseek_service
        self.gpt_service: Optional[GptService] = gpt_service
        self.gemini_service: Optional[GeminiService] = gemini_service

    async def extract_tags(self, text: str, topK: int = 5) -> str:
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
        tags: list[str] = jieba.analyse.extract_tags(text, topK=topK)
        return ",".join(tags)

    async def generate_ai_comments(self, article_id: int, db: Any) -> None:

        # 1. 判断是否需要生成AI评论
        ai_comments_count = (
            await self.comments_mapper.get_ai_comments_num_by_article_id_mapper_async(
                article_id, db
            )
        )
        if ai_comments_count > 0:
            Logger.info(Messages.ARTICLE_AI_COMMENT_EXISTS_DELETING(article_id))
            await self.comments_mapper.delete_ai_comments_by_article_id_mapper_async(
                article_id, db
            )
        # 2. 调用大模型生成AI评论
        # 2.1 获取文章标题,tags和内容
        article = await self.article_mapper.get_article_by_id_mapper_async(
            article_id, db
        )
        if not article:
            raise BusinessException(
                Messages.ARTICLE_NOT_EXISTS_ERROR,
                HttpCode.NOT_FOUND,
                Messages.ERROR_ARTICLE_NOT_FOUND,
            )
        # 2.2 构建提示词
        prompt = Prompts.ARTICLE_EVALUATION(
            article.title, article.tags, article.content
        )
        # 2.3 异步并发调用3个大模型生成AI评论
        Logger.info(Messages.CONCURRENT_LLM_AI_COMMENT_START(article_id))

        # 记录整体开始时间
        total_start_time = time.time()

        # 为每个模型创建带计时的包装函数
        async def timed_deepseek_call() -> Any:
            start = time.time()
            try:
                result = await self.deepseek_service.basic_chat(prompt)
                elapsed = time.time() - start
                Logger.info(Messages.LLM_CALL_COMPLETED("DeepSeek", elapsed))
                return result
            except Exception as e:
                elapsed = time.time() - start
                Logger.error(Messages.LLM_CALL_FAILED_TIMED("DeepSeek", elapsed, e))
                return e

        async def timed_gemini_call() -> Any:
            start = time.time()
            try:
                result = await self.gemini_service.basic_chat(prompt)
                elapsed = time.time() - start
                Logger.info(Messages.LLM_CALL_COMPLETED("Gemini", elapsed))
                return result
            except Exception as e:
                elapsed = time.time() - start
                Logger.error(Messages.LLM_CALL_FAILED_TIMED("Gemini", elapsed, e))
                return e

        async def timed_gpt_call() -> Any:
            start = time.time()
            try:
                result = await self.gpt_service.basic_chat(prompt)
                elapsed = time.time() - start
                Logger.info(Messages.LLM_CALL_COMPLETED("GPT", elapsed))
                return result
            except Exception as e:
                elapsed = time.time() - start
                Logger.error(Messages.LLM_CALL_FAILED_TIMED("GPT", elapsed, e))
                return e

        # 使用 asyncio.gather 并发执行三个异步调用
        responses = await asyncio.gather(
            timed_deepseek_call(),
            timed_gemini_call(),
            timed_gpt_call(),
            return_exceptions=True,  # 即使查个调用失败，其他调用仍继续
        )

        # 记录整体结束时间
        total_elapsed = time.time() - total_start_time
        Logger.info(
            Messages.CONCURRENT_LLM_ALL_COMPLETED(total_elapsed, article_id)
        )

        response_deepseek, response_gemini, response_gpt = responses

        # 检查是否有异常返回
        if isinstance(response_deepseek, Exception):
            Logger.error(Messages.LLM_FINAL_FAILED("DeepSeek", response_deepseek))
            response_deepseek = Messages.DEEPSEEK_CALL_FAILED_ERROR
        if isinstance(response_gemini, Exception):
            Logger.error(Messages.LLM_FINAL_FAILED("Gemini", response_gemini))
            response_gemini = Messages.GEMINI_CALL_FAILED_ERROR
        if isinstance(response_gpt, Exception):
            Logger.error(Messages.LLM_FINAL_FAILED("GPT", response_gpt))
            response_gpt = Messages.GPT_CALL_FAILED_ERROR

        # 2.4 解析大模型返回结果
        content_deepseek, star_deepseek = self._parse_ai_comment_response(
            response_deepseek
        )
        content_gemini, star_gemini = self._parse_ai_comment_response(response_gemini)
        content_gpt, star_gpt = self._parse_ai_comment_response(response_gpt)
        # 3. 构建AI评论对象
        deepseek_ai_comment: Any = Comments(
            article_id=article_id,
            user_id=1001,
            content=content_deepseek,
            star=star_deepseek,
            create_time=datetime.now(),
            update_time=datetime.now(),
        )
        gemini_ai_comment: Any = Comments(
            article_id=article_id,
            user_id=1002,
            content=content_gemini,
            star=star_gemini,
            create_time=datetime.now(),
            update_time=datetime.now(),
        )
        gpt_ai_comment: Any = Comments(
            article_id=article_id,
            user_id=1003,
            content=content_gpt,
            star=star_gpt,
            create_time=datetime.now(),
            update_time=datetime.now(),
        )

        # 4. 保存AI评论到数据库（独立 Session 并行插入，互不干扰）
        async def _insert_comment(comment: Comments) -> None:
            async with AsyncSessionLocal() as session:
                await self.comments_mapper.create_comment_mapper_async(comment, session)

        await asyncio.gather(
            _insert_comment(deepseek_ai_comment),
            _insert_comment(gemini_ai_comment),
            _insert_comment(gpt_ai_comment),
        )
        Logger.info(Messages.AI_COMMENT_GENERATED_AND_SAVED(article_id))

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

    async def generate_ai_comments_with_reference(
        self, article_id: int, db: Any
    ) -> None:
        """
        基于权威参考文本生成AI评论
        获取文章的子分类权威参考文本，提取内容，然后调用AI服务进行评价

        Args:
            article_id: 文章ID
            db: 数据库会话
        """
        # 延迟导入避免循环依赖
        from app.internal.models import Comments

        # 1. 判断是否需要生成AI评论
        ai_comments_count = (
            await self.comments_mapper.get_ai_comments_num_by_article_id_mapper_async(
                article_id, db
            )
        )
        if ai_comments_count > 0:
            Logger.info(Messages.ARTICLE_AI_COMMENT_EXISTS_DELETING(article_id))
            await self.comments_mapper.delete_ai_comments_by_article_id_mapper_async(
                article_id, db
            )

        # 2. 获取文章信息
        article = await self.article_mapper.get_article_by_id_mapper_async(
            article_id, db
        )
        if not article:
            Logger.error(Messages.ARTICLE_NOT_FOUND_WITH_ID(article_id))
            return

        Logger.info(Messages.REFERENCE_BASED_AI_COMMENT_START(article_id))

        # 3. 获取权威参考文本
        category_ref_mapper: CategoryReferenceMapper = get_category_reference_mapper()
        reference_content = None

        # 获取文章的子分类ID
        sub_category_id = (
            article.sub_category_id if hasattr(article, "sub_category_id") else None
        )

        if sub_category_id:
            category_ref = await category_ref_mapper.get_category_reference_by_sub_category_id_mapper_async(
                sub_category_id, db
            )

            if category_ref:
                Logger.info(Messages.REFERENCE_TEXT_TYPE_FOUND(str(category_ref.get('type'))))
                Logger.info(Messages.REFERENCE_TEXT_DETAIL(category_ref))

                # 4. 根据类型提取内容并使用大模型进行总结
                extractor = get_reference_content_extractor()
                ref_type = category_ref.get("type", "link")
                ref_value = None

                if ref_type == "pdf":
                    ref_value = category_ref.get("pdf")
                    Logger.info(Messages.REFERENCE_PDF_EXTRACTION_START(str(ref_value)))
                elif ref_type == "link":
                    ref_value = category_ref.get("link")
                    Logger.info(Messages.REFERENCE_LINK_EXTRACTION_START(str(ref_value)))

                # 定义三个大模型的总结函数
                async def summarize_with_deepseek(content: str) -> str:
                    try:
                        return await self.deepseek_service.summarize_content(
                            content, max_length=1500
                        )
                    except Exception as e:
                        Logger.error(Messages.LLM_SUMMARIZE_FAILED("DeepSeek", e))
                        return content[:1500]

                async def summarize_with_gemini(content: str) -> str:
                    try:
                        return await self.gemini_service.summarize_content(
                            content, max_length=1500
                        )
                    except Exception as e:
                        Logger.error(Messages.LLM_SUMMARIZE_FAILED("Gemini", e))
                        return content[:1500]

                async def summarize_with_gpt(content: str) -> str:
                    try:
                        return await self.gpt_service.summarize_content(
                            content, max_length=1500
                        )
                    except Exception as e:
                        Logger.error(Messages.LLM_SUMMARIZE_FAILED("GPT", e))
                        return content[:1500]

                # 并发调用三个大模型对提取的内容进行总结
                summarize_tasks = [
                    extractor.extract_reference_content(
                        ref_type, ref_value, 3000, summarize_with_deepseek
                    ),
                    extractor.extract_reference_content(
                        ref_type, ref_value, 3000, summarize_with_gemini
                    ),
                    extractor.extract_reference_content(
                        ref_type, ref_value, 3000, summarize_with_gpt
                    ),
                ]

                summary_results = await asyncio.gather(
                    *summarize_tasks, return_exceptions=True
                )

                # 合并三个大模型的总结结果
                summaries = []
                if isinstance(summary_results[0], str) and summary_results[0]:
                    summaries.append(Messages.LLM_SUMMARY_RESULT_ENTRY("DeepSeek", summary_results[0]))
                if isinstance(summary_results[1], str) and summary_results[1]:
                    summaries.append(Messages.LLM_SUMMARY_RESULT_ENTRY("Gemini", summary_results[1]))
                if isinstance(summary_results[2], str) and summary_results[2]:
                    summaries.append(Messages.LLM_SUMMARY_RESULT_ENTRY("GPT", summary_results[2]))

                if summaries:
                    reference_content = "\n\n".join(summaries)
                    Logger.info(
                        Messages.REFERENCE_TEXT_EXTRACTED_AND_SUMMARIZED(len(reference_content))
                    )
                else:
                    Logger.warning(Messages.REFERENCE_TEXT_EXTRACTION_FAILED_TYPE(ref_type))
                    reference_content = (
                        Messages.REFERENCE_TEXT_FALLBACK_CONTENT(ref_type, str(ref_value))
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
            article.title, article.tags, article.content
        )

        # 6. 异步并发调用3个大模型生成AI评论
        Logger.info(
            Messages.CONCURRENT_LLM_REFERENCE_AI_COMMENT_START(article_id)
        )

        total_start_time = time.time()

        async def timed_deepseek_ref_call() -> Any:
            start = time.time()
            try:
                result = await self.deepseek_service.with_reference_chat(
                    article_content, reference_content
                )
                elapsed = time.time() - start
                Logger.info(Messages.LLM_REFERENCE_CALL_COMPLETED("DeepSeek", elapsed))
                return result
            except Exception as e:
                elapsed = time.time() - start
                Logger.error(
                    Messages.LLM_REFERENCE_CALL_FAILED_TIMED("DeepSeek", elapsed, e)
                )
                return e

        async def timed_gemini_ref_call() -> Any:
            start = time.time()
            try:
                result = await self.gemini_service.with_reference_chat(
                    article_content, reference_content
                )
                elapsed = time.time() - start
                Logger.info(Messages.LLM_REFERENCE_CALL_COMPLETED("Gemini", elapsed))
                return result
            except Exception as e:
                elapsed = time.time() - start
                Logger.error(
                    Messages.LLM_REFERENCE_CALL_FAILED_TIMED("Gemini", elapsed, e)
                )
                return e

        async def timed_gpt_ref_call() -> Any:
            start = time.time()
            try:
                result = await self.gpt_service.with_reference_chat(
                    article_content, reference_content
                )
                elapsed = time.time() - start
                Logger.info(Messages.LLM_REFERENCE_CALL_COMPLETED("GPT", elapsed))
                return result
            except Exception as e:
                elapsed = time.time() - start
                Logger.error(Messages.LLM_REFERENCE_CALL_FAILED_TIMED("GPT", elapsed, e))
                return e

        # 并发执行三个调用
        responses = await asyncio.gather(
            timed_deepseek_ref_call(),
            timed_gemini_ref_call(),
            timed_gpt_ref_call(),
            return_exceptions=True,
        )

        total_elapsed = time.time() - total_start_time
        Logger.info(
            Messages.CONCURRENT_LLM_REFERENCE_ALL_COMPLETED(total_elapsed, article_id)
        )

        response_deepseek, response_gemini, response_gpt = responses

        # 检查异常返回
        if isinstance(response_deepseek, Exception):
            Logger.error(Messages.LLM_REFERENCE_FINAL_FAILED("DeepSeek", response_deepseek))
            response_deepseek = Messages.DEEPSEEK_CALL_FAILED_ERROR
        if isinstance(response_gemini, Exception):
            Logger.error(Messages.LLM_REFERENCE_FINAL_FAILED("Gemini", response_gemini))
            response_gemini = Messages.GEMINI_CALL_FAILED_ERROR
        if isinstance(response_gpt, Exception):
            Logger.error(Messages.LLM_REFERENCE_FINAL_FAILED("GPT", response_gpt))
            response_gpt = Messages.GPT_CALL_FAILED_ERROR

        # 7. 解析大模型返回结果
        content_deepseek, star_deepseek = self._parse_ai_comment_response(
            response_deepseek
        )
        content_gemini, star_gemini = self._parse_ai_comment_response(response_gemini)
        content_gpt, star_gpt = self._parse_ai_comment_response(response_gpt)

        # 8. 构建AI评论对象
        deepseek_ai_comment: Any = Comments(
            article_id=article_id,
            user_id=1001,
            content=content_deepseek,
            star=star_deepseek,
            create_time=datetime.now(),
            update_time=datetime.now(),
        )
        gemini_ai_comment: Any = Comments(
            article_id=article_id,
            user_id=1002,
            content=content_gemini,
            star=star_gemini,
            create_time=datetime.now(),
            update_time=datetime.now(),
        )
        gpt_ai_comment: Any = Comments(
            article_id=article_id,
            user_id=1003,
            content=content_gpt,
            star=star_gpt,
            create_time=datetime.now(),
            update_time=datetime.now(),
        )

        # 9. 保存AI评论到数据库（独立 Session 并行插入，互不干扰）
        async def _insert_comment_ref(comment: Comments) -> None:
            async with AsyncSessionLocal() as session:
                await self.comments_mapper.create_comment_mapper_async(comment, session)

        await asyncio.gather(
            _insert_comment_ref(deepseek_ai_comment),
            _insert_comment_ref(gemini_ai_comment),
            _insert_comment_ref(gpt_ai_comment),
        )
        Logger.info(Messages.REFERENCE_AI_COMMENT_GENERATED_AND_SAVED(article_id))

    async def generate_authority_article_with_ai_summaries(
        self, reference_type: str, reference_value: str
    ) -> Dict[str, Any]:
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
                Messages.AUTHORITY_ARTICLE_GENERATION_START(reference_type, reference_value)
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

            async def timed_deepseek_summarize() -> Optional[str]:
                start = time.time()
                try:
                    result = await self.deepseek_service.summarize_content(
                        raw_content, max_length=1500
                    )
                    elapsed = time.time() - start
                    Logger.info(
                        Messages.LLM_SUMMARIZE_COMPLETED("DeepSeek", elapsed, len(result) if result else 0)
                    )
                    return result
                except Exception as e:
                    elapsed = time.time() - start
                    Logger.error(Messages.LLM_SUMMARIZE_FAILED_TIMED("DeepSeek", elapsed, e))
                    return None

            async def timed_gemini_summarize() -> Optional[str]:
                start = time.time()
                try:
                    result = await self.gemini_service.summarize_content(
                        raw_content, max_length=1500
                    )
                    elapsed = time.time() - start
                    Logger.info(
                        Messages.LLM_SUMMARIZE_COMPLETED("Gemini", elapsed, len(result) if result else 0)
                    )
                    return result
                except Exception as e:
                    elapsed = time.time() - start
                    Logger.error(Messages.LLM_SUMMARIZE_FAILED_TIMED("Gemini", elapsed, e))
                    return None

            async def timed_gpt_summarize() -> Optional[str]:
                start = time.time()
                try:
                    result = await self.gpt_service.summarize_content(
                        raw_content, max_length=1500
                    )
                    elapsed = time.time() - start
                    Logger.info(
                        Messages.LLM_SUMMARIZE_COMPLETED("GPT", elapsed, len(result) if result else 0)
                    )
                    return result
                except Exception as e:
                    elapsed = time.time() - start
                    Logger.error(Messages.LLM_SUMMARIZE_FAILED_TIMED("GPT", elapsed, e))
                    return None

            # 并发执行三个总结任务
            summaries = await asyncio.gather(
                timed_deepseek_summarize(),
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
                    "deepseek": {
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
            return {"status": "error", "message": Messages.AUTHORITY_ARTICLE_GENERATION_FAILED(str(e))}


@lru_cache()
def get_generate_service(
    comments_mapper: CommentsMapper = Depends(get_comments_mapper),
    article_mapper: ArticleMapper = Depends(get_article_mapper),
    deepseek_service: DeepseekService = Depends(get_deepseek_service),
    gemini_service: GeminiService = Depends(get_gemini_service),
    gpt_service: GptService = Depends(get_gpt_service),
) -> GenerateService:
    return GenerateService(
        comments_mapper,
        article_mapper,
        deepseek_service,
        gemini_service,
        gpt_service,
    )

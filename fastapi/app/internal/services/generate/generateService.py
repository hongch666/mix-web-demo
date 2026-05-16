import asyncio
import re
import time
from functools import lru_cache
from typing import Any, Dict, Optional

import jieba.analyse
from app.core.base import Constants, HttpCode, Logger
from app.core.errors import BusinessException
from app.internal.agents import get_reference_content_extractor
from app.internal.clients import SpringClient

from fastapi import Depends

from ..llm.extend.deepseekService import DeepseekService, get_deepseek_service
from ..llm.extend.geminiService import GeminiService, get_gemini_service
from ..llm.extend.gptService import GptService, get_gpt_service


class GenerateService:
    """生成 Service"""

    def __init__(
        self,
        deepseek_service: Optional[DeepseekService] = None,
        gemini_service: Optional[GeminiService] = None,
        gpt_service: Optional[GptService] = None,
    ) -> None:
        self.deepseek_service: Optional[DeepseekService] = deepseek_service
        self.gpt_service: Optional[GptService] = gpt_service
        self.gemini_service: Optional[GeminiService] = gemini_service
        self._spring_client: SpringClient = SpringClient()

    async def extract_tags(self, text: str, topK: int = 5) -> str:
        text = re.sub(
            r"(```[\s\S]*?```|`[^`]*`|\!\[[^\]]*\]\([^\)]*\)|\[[^\]]*\]\([^\)]*\)|[#>*_~\-\+\=\[\]`]|\d+\.|\n)",
            " ",
            text,
        )
        text = re.sub(r"\s+", " ", text).strip()
        tags: list[str] = jieba.analyse.extract_tags(text, topK=topK)
        return ",".join(tags)

    async def generate_ai_comments(self, article_id: int, db: Any = None) -> None:
        article = await self._get_article_context(article_id)
        prompt = f"""请对以下文章进行评价，并给出评分。
        要求：
        1. 给出简短的评价（100-200字）
        2. 给出0-10分的评分（可以是小数）
        3. 请使用以下格式输出：
            评价内容：[你的评价]
            评分：[你的评分]
        文章标题：{article.get("title")}
        文章标签：{article.get("tags")}
        文章内容：{article.get("content")}
        """

        comments = await self._generate_three_model_comments(prompt, article_id)
        await self._spring_client.replace_ai_comments(article_id, comments)
        Logger.info(f"AI评论生成并保存完成，文章ID：{article_id}")

    async def generate_ai_comments_with_reference(
        self, article_id: int, db: Any = None
    ) -> None:
        article = await self._get_article_context(article_id)
        reference_content = await self._build_reference_content(article)

        article_content = f"""
                        标题：{article.get("title")}
                        标签：{article.get("tags")}
                        内容摘要（前500字）：{str(article.get("content") or "")[:500] or "无"}
                        """

        Logger.info(
            f"开始并发调用3个大模型生成AI评论（基于参考文本），文章ID：{article_id}"
        )
        responses = await asyncio.gather(
            self._timed_call(
                "DeepSeek参考文本",
                self.deepseek_service.with_reference_chat(
                    article_content, reference_content
                ),
            ),
            self._timed_call(
                "Gemini参考文本",
                self.gemini_service.with_reference_chat(
                    article_content, reference_content
                ),
            ),
            self._timed_call(
                "GPT参考文本",
                self.gpt_service.with_reference_chat(article_content, reference_content),
            ),
            return_exceptions=True,
        )

        comments = self._build_ai_comment_payload(responses)
        await self._spring_client.replace_ai_comments(article_id, comments)
        Logger.info(f"基于参考文本的AI评论生成并保存完成，文章ID：{article_id}")

    async def generate_authority_article_with_ai_summaries(
        self, reference_type: str, reference_value: str
    ) -> Dict[str, Any]:
        try:
            Logger.info(
                f"开始生成权威文章，类型: {reference_type}，值: {reference_value}"
            )
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
                return {
                    "status": "error",
                    "message": f"不支持的参考文本类型: {reference_type}",
                }

            if not raw_content:
                return {
                    "status": "error",
                    "message": Constants.REFERENCE_TEXT_EXTRACTION_ERROR,
                }

            total_start_time = time.time()
            summaries = await asyncio.gather(
                self._safe_summarize("DeepSeek", raw_content, self.deepseek_service),
                self._safe_summarize("Gemini", raw_content, self.gemini_service),
                self._safe_summarize("GPT", raw_content, self.gpt_service),
            )
            total_elapsed = time.time() - total_start_time

            Logger.info(Constants.CONCURRENT_CHAT_MESSAGE_SUCCESS)
            return {
                "status": "success",
                "reference_type": reference_type,
                "reference_value": reference_value,
                "raw_content_length": len(raw_content),
                "raw_content_preview": raw_content[:500],
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
        except Exception as e:
            Logger.error(f"生成权威文章异常: {str(e)}")
            return {"status": "error", "message": f"生成权威文章失败: {str(e)}"}

    async def _get_article_context(self, article_id: int) -> Dict[str, Any]:
        article = await self._spring_client.get_ai_comment_context(article_id)
        if not article:
            raise BusinessException(
                Constants.ARTICLE_NOT_EXISTS_ERROR,
                HttpCode.NOT_FOUND,
                Constants.ERROR_ARTICLE_NOT_FOUND,
            )
        return article

    async def _build_reference_content(self, article: Dict[str, Any]) -> str:
        category_ref = article.get("categoryReference")
        if not category_ref:
            return Constants.CATEGORY_NO_AUTHORITATIVE_REFERENCE_TEXT_ERROR

        extractor = get_reference_content_extractor()
        ref_type = category_ref.get("type", "link")
        ref_value = category_ref.get("pdf") if ref_type == "pdf" else category_ref.get("link")
        if not ref_value:
            return Constants.CATEGORY_NO_AUTHORITATIVE_REFERENCE_TEXT_ERROR

        async def summarize_with_service(content: str, service: Any) -> str:
            try:
                return await service.summarize_content(content, max_length=1500)
            except Exception as e:
                Logger.error(f"参考文本总结失败: {e}")
                return content[:1500]

        summary_results = await asyncio.gather(
            extractor.extract_reference_content(
                ref_type,
                ref_value,
                3000,
                lambda content: summarize_with_service(content, self.deepseek_service),
            ),
            extractor.extract_reference_content(
                ref_type,
                ref_value,
                3000,
                lambda content: summarize_with_service(content, self.gemini_service),
            ),
            extractor.extract_reference_content(
                ref_type,
                ref_value,
                3000,
                lambda content: summarize_with_service(content, self.gpt_service),
            ),
            return_exceptions=True,
        )
        summaries = [
            str(item)
            for item in summary_results
            if isinstance(item, str) and item.strip()
        ]
        return (
            "\n\n".join(summaries)
            if summaries
            else Constants.CATEGORY_NO_AUTHORITATIVE_REFERENCE_TEXT_ERROR
        )

    async def _generate_three_model_comments(
        self, prompt: str, article_id: int
    ) -> list[Dict[str, Any]]:
        Logger.info(f"开始并发调用3个大模型生成AI评论，文章ID：{article_id}")
        responses = await asyncio.gather(
            self._timed_call("DeepSeek", self.deepseek_service.basic_chat(prompt)),
            self._timed_call("Gemini", self.gemini_service.basic_chat(prompt)),
            self._timed_call("GPT", self.gpt_service.basic_chat(prompt)),
            return_exceptions=True,
        )
        return self._build_ai_comment_payload(responses)

    async def _timed_call(self, name: str, coroutine: Any) -> Any:
        start = time.time()
        try:
            result = await coroutine
            Logger.info(f"{name}调用完成，耗时: {time.time() - start:.2f}秒")
            return result
        except Exception as e:
            Logger.error(f"{name}调用失败，耗时: {time.time() - start:.2f}秒，错误: {e}")
            return e

    async def _safe_summarize(self, name: str, content: str, service: Any) -> Optional[str]:
        try:
            result = await service.summarize_content(content, max_length=1500)
            Logger.info(f"{name}总结完成，长度: {len(result) if result else 0}")
            return result
        except Exception as e:
            Logger.error(f"{name}总结失败: {e}")
            return None

    def _build_ai_comment_payload(self, responses: list[Any]) -> list[Dict[str, Any]]:
        fallback = [
            Constants.DEEPSEEK_CALL_FAILED_ERROR,
            Constants.GEMINI_CALL_FAILED_ERROR,
            Constants.GPT_CALL_FAILED_ERROR,
        ]
        user_ids = [1001, 1002, 1003]
        comments: list[Dict[str, Any]] = []
        for index, response in enumerate(responses):
            final_response = fallback[index] if isinstance(response, Exception) else response
            content, star = self._parse_ai_comment_response(str(final_response))
            comments.append({"userId": user_ids[index], "content": content, "star": star})
        return comments

    def _parse_ai_comment_response(self, response: str) -> tuple[str, float]:
        content = ""
        star = 6.0
        content_match = re.search(
            r"评价内容[：:]\s*(.+?)(?=评分|$)", response, re.DOTALL
        )
        if content_match:
            content = content_match.group(1).strip()
        else:
            lines = response.split("\n")
            content = " ".join(
                line.strip()
                for line in lines
                if "评分" not in line and line.strip()
            )[:200].strip()

        star_match = re.search(r"评分[：:]\s*(\d+(?:\.\d+)?)", response)
        if star_match:
            star = float(star_match.group(1))
        else:
            score_match = re.search(r"(\d+(?:\.\d+)?)\s*分", response)
            if score_match:
                star = float(score_match.group(1))

        return content or response[:200], star


@lru_cache()
def get_generate_service(
    deepseek_service: DeepseekService = Depends(get_deepseek_service),
    gemini_service: GeminiService = Depends(get_gemini_service),
    gpt_service: GptService = Depends(get_gpt_service),
) -> GenerateService:
    return GenerateService(
        deepseek_service=deepseek_service,
        gemini_service=gemini_service,
        gpt_service=gpt_service,
    )

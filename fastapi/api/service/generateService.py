from functools import lru_cache
from typing import Any
import re
import asyncio
import time
from datetime import datetime
from fastapi import Depends
import jieba.analyse
from common.utils import fileLogger as logger
from .doubaoService import DoubaoService, get_doubao_service
from .geminiService import GeminiService, get_gemini_service
from .qwenService import QwenService, get_qwen_service
from api.mapper import (
    CommentsMapper, get_comments_mapper,
    ArticleMapper, get_article_mapper
)

class GenerateService:
    """生成 Service"""

    def __init__(
            self, 
            comments_mapper: CommentsMapper = None, 
            article_mapper: ArticleMapper = None, 
            doubao_service: DoubaoService = None, 
            gemini_service: GeminiService = None, 
            qwen_service: QwenService = None
        ):
        self.comments_mapper = comments_mapper
        self.article_mapper = article_mapper
        self.doubao_service = doubao_service
        self.gemini_service = gemini_service
        self.qwen_service = qwen_service

    def extract_tags(self,text: str, topK: int = 5) -> str:
        """
        提取文本中的关键词作为tags
        :param text: 文章内容
        :param topK: 返回关键词数量
        :return: 关键词列表
        """
        # 去除markdown格式符号
        text = re.sub(r'(```[\s\S]*?```|`[^`]*`|\!\[[^\]]*\]\([^\)]*\)|\[[^\]]*\]\([^\)]*\)|[#>*_~\-\+\=\[\]`]|\d+\.|\n)', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        tags: list[str] = jieba.analyse.extract_tags(text, topK=topK)
        return ",".join(tags)

    async def generate_ai_comments(self, article_id: int, db: Any):
        # 延迟导入避免循环依赖
        from entity.po import Comments
        
        # 1. 判断是否需要生成AI评论
        ai_comments_count = self.comments_mapper.get_ai_comments_num_by_article_id_mapper(article_id, db)
        if ai_comments_count > 0:
            logger.info(f"文章ID：{article_id} 已存在AI评论，删除对应AI评论")
            self.comments_mapper.delete_ai_comments_by_article_id_mapper(article_id, db)
        # 2. 调用大模型生成AI评论
        # 2.1 获取文章标题,tags和内容
        article = self.article_mapper.get_article_by_id_mapper(article_id, db)
        if not article:
            raise Exception("文章不存在")
        # 2.2 构建提示词
        prompt = f"""请对以下文章进行评价，并给出评分。
        要求：
        1. 给出简短的评价（100-200字）
        2. 给出0-10分的评分（可以是小数）
        3. 请使用以下格式输出：
            评价内容：[你的评价]
            评分：[你的评分]
        文章标题：{article.title}
        文章标签：{article.tags}
        文章内容：{article.content}
        """
        # 2.3 异步并发调用3个大模型生成AI评论
        logger.info(f"开始并发调用3个大模型生成AI评论，文章ID：{article_id}")
        
        # 记录整体开始时间
        total_start_time = time.time()
        
        # 为每个模型创建带计时的包装函数
        async def timed_doubao_call():
            start = time.time()
            try:
                result = await self.doubao_service.basic_chat(prompt)
                elapsed = time.time() - start
                logger.info(f"豆包调用完成，耗时: {elapsed:.2f}秒")
                return result
            except Exception as e:
                elapsed = time.time() - start
                logger.error(f"豆包调用失败，耗时: {elapsed:.2f}秒，错误: {e}")
                return e
        
        async def timed_gemini_call():
            start = time.time()
            try:
                result = await self.gemini_service.basic_chat(prompt)
                elapsed = time.time() - start
                logger.info(f"Gemini调用完成，耗时: {elapsed:.2f}秒")
                return result
            except Exception as e:
                elapsed = time.time() - start
                logger.error(f"Gemini调用失败，耗时: {elapsed:.2f}秒，错误: {e}")
                return e
        
        async def timed_qwen_call():
            start = time.time()
            try:
                result = await self.qwen_service.basic_chat(prompt)
                elapsed = time.time() - start
                logger.info(f"Qwen调用完成，耗时: {elapsed:.2f}秒")
                return result
            except Exception as e:
                elapsed = time.time() - start
                logger.error(f"Qwen调用失败，耗时: {elapsed:.2f}秒，错误: {e}")
                return e
        
        # 使用 asyncio.gather 并发执行三个异步调用
        responses = await asyncio.gather(
            timed_doubao_call(),
            timed_gemini_call(),
            timed_qwen_call(),
            return_exceptions=True  # 即使查个调用失败，其他调用仍继续
        )
        
        # 记录整体结束时间
        total_elapsed = time.time() - total_start_time
        logger.info(f"3个大模型并发调用全部完成，总耗时: {total_elapsed:.2f}秒，文章ID：{article_id}")
        
        response_doubao, response_gemini, response_qwen = responses
        
        # 检查是否有异常返回
        if isinstance(response_doubao, Exception):
            logger.error(f"豆包大模型最终失败: {response_doubao}")
            response_doubao = "豆包调用失败"
        if isinstance(response_gemini, Exception):
            logger.error(f"Gemini大模型最终失败: {response_gemini}")
            response_gemini = "Gemini调用失败"
        if isinstance(response_qwen, Exception):
            logger.error(f"Qwen大模型最终失败: {response_qwen}")
            response_qwen = "Qwen调用失败"
        
        # 2.4 解析大模型返回结果
        content_doubao, star_doubao = self._parse_ai_comment_response(response_doubao)
        content_gemini, star_gemini = self._parse_ai_comment_response(response_gemini)
        content_qwen, star_qwen = self._parse_ai_comment_response(response_qwen)
        # 3. 构建AI评论对象
        doubao_ai_comment: Any = Comments(
            article_id=article_id,
            user_id=1001,
            content=content_doubao,
            star=star_doubao,
            create_time=datetime.now(),
            update_time=datetime.now()
        )
        gemini_ai_comment: Any = Comments(
            article_id=article_id,
            user_id=1002,
            content=content_gemini,
            star=star_gemini,
            create_time=datetime.now(),
            update_time=datetime.now()
        )
        qwen_ai_comment: Any = Comments(
            article_id=article_id,
            user_id=1003,
            content=content_qwen,
            star=star_qwen,
            create_time=datetime.now(),
            update_time=datetime.now()
        )
        # 4. 保存AI评论到数据库
        self.comments_mapper.create_comment_mapper(doubao_ai_comment, db)
        self.comments_mapper.create_comment_mapper(gemini_ai_comment, db)
        self.comments_mapper.create_comment_mapper(qwen_ai_comment, db)
        logger.info(f"AI评论生成并保存完成，文章ID：{article_id}")
        
    # 定义工具函数解析大模型返回结果
    def _parse_ai_comment_response(self, response: str) -> tuple[str, float]:
        content = ""
        star = 6.0
        # 提取评价内容
        content_match = re.search(r'评价内容[：:]\s*(.+?)(?=评分|$)', response, re.DOTALL)
        if content_match:
            content = content_match.group(1).strip()
        else:
            # 如果没有找到标记，使用整个响应的前200字
            lines = response.split('\n')
            for line in lines:
                if '评分' not in line and line.strip():
                    content += line.strip() + " "
            content = content[:200].strip()
        
        # 提取评分
        star_match = re.search(r'评分[：:]\s*(\d+(?:\.\d+)?)', response)
        if star_match:
            star = float(star_match.group(1))
        else:
            # 尝试查找任何数字后跟"分"的模式
            score_match = re.search(r'(\d+(?:\.\d+)?)\s*分', response)
            if score_match:
                star = float(score_match.group(1))
        
        if not content:
            content = response[:200]
        
        return content, star

@lru_cache()
def get_generate_service(
        comments_mapper: CommentsMapper = Depends(get_comments_mapper), 
        article_mapper: ArticleMapper = Depends(get_article_mapper), 
        doubao_service: DoubaoService = Depends(get_doubao_service), 
        gemini_service: GeminiService = Depends(get_gemini_service), 
        qwen_service: QwenService = Depends(get_qwen_service)
    ) -> GenerateService:
    return GenerateService(
            comments_mapper, 
            article_mapper, 
            doubao_service, 
            gemini_service, 
            qwen_service
        )
from functools import lru_cache
from typing import Any
import re
import asyncio
import time
from datetime import datetime
from fastapi import Depends
from api.mapper import CommentsMapper, get_comments_mapper, ArticleMapper, get_article_mapper
from api.service import CozeService, get_coze_service, GeminiService, get_gemini_service, TongyiService, get_tongyi_service
from entity.po import Comments
from common.utils import fileLogger as logger

class AiCommentService:
    def __init__(self, comments_mapper: CommentsMapper, article_mapper: ArticleMapper, coze_service: CozeService, gemini_service: GeminiService, tongyi_service: TongyiService):
        self.comments_mapper = comments_mapper
        self.article_mapper = article_mapper
        self.coze_service = coze_service
        self.gemini_service = gemini_service
        self.tongyi_service = tongyi_service

    async def generate_ai_comments(self, article_id: int, db: Any):
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
        async def timed_coze_call():
            start = time.time()
            try:
                result = await self.coze_service.basic_chat(prompt)
                elapsed = time.time() - start
                logger.info(f"Coze调用完成，耗时: {elapsed:.2f}秒")
                return result
            except Exception as e:
                elapsed = time.time() - start
                logger.error(f"Coze调用失败，耗时: {elapsed:.2f}秒，错误: {e}")
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
        
        async def timed_tongyi_call():
            start = time.time()
            try:
                result = await self.tongyi_service.basic_chat(prompt)
                elapsed = time.time() - start
                logger.info(f"通义千问调用完成，耗时: {elapsed:.2f}秒")
                return result
            except Exception as e:
                elapsed = time.time() - start
                logger.error(f"通义千问调用失败，耗时: {elapsed:.2f}秒，错误: {e}")
                return e
        
        # 使用 asyncio.gather 并发执行三个异步调用
        responses = await asyncio.gather(
            timed_coze_call(),
            timed_gemini_call(),
            timed_tongyi_call(),
            return_exceptions=True  # 即使某个调用失败，其他调用仍继续
        )
        
        # 记录整体结束时间
        total_elapsed = time.time() - total_start_time
        logger.info(f"3个大模型并发调用全部完成，总耗时: {total_elapsed:.2f}秒，文章ID：{article_id}")
        
        response_coze, response_gemini, response_tongyi = responses
        
        # 检查是否有异常返回
        if isinstance(response_coze, Exception):
            logger.error(f"Coze大模型最终失败: {response_coze}")
            response_coze = "Coze调用失败"
        if isinstance(response_gemini, Exception):
            logger.error(f"Gemini大模型最终失败: {response_gemini}")
            response_gemini = "Gemini调用失败"
        if isinstance(response_tongyi, Exception):
            logger.error(f"通义千问大模型最终失败: {response_tongyi}")
            response_tongyi = "通义千问调用失败"
        
        # 2.4 解析大模型返回结果
        content_coze, star_coze = self._parse_ai_comment_response(response_coze)
        content_gemini, star_gemini = self._parse_ai_comment_response(response_gemini)
        content_tongyi, star_tongyi = self._parse_ai_comment_response(response_tongyi)
        # 3. 构建AI评论对象
        coze_ai_comment: Comments = Comments(
            article_id=article_id,
            user_id=1001,
            content=content_coze,
            star=star_coze,
            create_time=datetime.now(),
            update_time=datetime.now()
        )
        gemini_ai_comment: Comments = Comments(
            article_id=article_id,
            user_id=1002,
            content=content_gemini,
            star=star_gemini,
            create_time=datetime.now(),
            update_time=datetime.now()
        )
        tongyi_ai_comment: Comments = Comments(
            article_id=article_id,
            user_id=1003,
            content=content_tongyi,
            star=star_tongyi,
            create_time=datetime.now(),
            update_time=datetime.now()
        )
        # 4. 保存AI评论到数据库
        self.comments_mapper.create_comment_mapper(coze_ai_comment, db)
        self.comments_mapper.create_comment_mapper(gemini_ai_comment, db)
        self.comments_mapper.create_comment_mapper(tongyi_ai_comment, db)
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

    
@lru_cache
def get_ai_comment_service(comments_mapper: CommentsMapper = Depends(get_comments_mapper), article_mapper: ArticleMapper = Depends(get_article_mapper), coze_service: CozeService = Depends(get_coze_service), gemini_service: GeminiService = Depends(get_gemini_service), tongyi_service: TongyiService = Depends(get_tongyi_service)) -> AiCommentService:
    return AiCommentService(comments_mapper, article_mapper, coze_service, gemini_service, tongyi_service)
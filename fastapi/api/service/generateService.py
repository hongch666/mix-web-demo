from functools import lru_cache
from typing import Any, Dict, Optional
import re
import asyncio
import time
from datetime import datetime
from fastapi import Depends
import jieba.analyse
from common.utils import fileLogger as logger, Constants
from common.agent import get_reference_content_extractor
from .doubaoService import DoubaoService, get_doubao_service
from .geminiService import GeminiService, get_gemini_service
from .qwenService import QwenService, get_qwen_service
from api.mapper import (
    CommentsMapper, get_comments_mapper,
    ArticleMapper, get_article_mapper,
    CategoryReferenceMapper, get_category_reference_mapper
)
from common.exceptions import BusinessException

class GenerateService:
    """生成 Service"""

    def __init__(
            self, 
            comments_mapper: Optional[CommentsMapper] = None, 
            article_mapper: Optional[ArticleMapper] = None, 
            doubao_service: Optional[DoubaoService] = None, 
            gemini_service: Optional[GeminiService] = None, 
            qwen_service: Optional[QwenService] = None
        ):
        self.comments_mapper: Optional[CommentsMapper] = comments_mapper
        self.article_mapper: Optional[ArticleMapper] = article_mapper
        self.doubao_service: Optional[DoubaoService] = doubao_service
        self.gemini_service: Optional[GeminiService] = gemini_service
        self.qwen_service: Optional[QwenService] = qwen_service

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

    async def generate_ai_comments(self, article_id: int, db: Any) -> None:
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
            raise BusinessException("文章不存在")
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
        async def timed_doubao_call() -> Any:
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
        
        async def timed_gemini_call() -> Any:
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
        
        async def timed_qwen_call() -> Any:
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
            response_doubao = Constants.DOUBAO_CALL_FAILED_ERROR
        if isinstance(response_gemini, Exception):
            logger.error(f"Gemini大模型最终失败: {response_gemini}")
            response_gemini = Constants.GEMINI_CALL_FAILED_ERROR
        if isinstance(response_qwen, Exception):
            logger.error(f"Qwen大模型最终失败: {response_qwen}")
            response_qwen = Constants.QWEN_CALL_FAILED_ERROR
        
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

    async def generate_ai_comments_with_reference(self, article_id: int, db: Any) -> None:
        """
        基于权威参考文本生成AI评论
        获取文章的子分类权威参考文本，提取内容，然后调用AI服务进行评价
        
        Args:
            article_id: 文章ID
            db: 数据库会话
        """
        # 延迟导入避免循环依赖
        from entity.po import Comments
        
        # 1. 判断是否需要生成AI评论
        ai_comments_count = self.comments_mapper.get_ai_comments_num_by_article_id_mapper(article_id, db)
        if ai_comments_count > 0:
            logger.info(f"文章ID：{article_id} 已存在AI评论，删除对应AI评论")
            self.comments_mapper.delete_ai_comments_by_article_id_mapper(article_id, db)
        
        # 2. 获取文章信息
        article = self.article_mapper.get_article_by_id_mapper(article_id, db)
        if not article:
            logger.error(f"文章不存在: {article_id}")
            return
        
        logger.info(f"开始基于参考文本生成AI评论，文章ID：{article_id}")
        
        # 3. 获取权威参考文本
        category_ref_mapper: CategoryReferenceMapper = get_category_reference_mapper()
        reference_content = None
        
        # 获取文章的子分类ID
        sub_category_id = article.sub_category_id if hasattr(article, 'sub_category_id') else None
        
        if sub_category_id:
            category_ref = category_ref_mapper.get_category_reference_by_sub_category_id_mapper(
                sub_category_id, db
            )
            
            if category_ref:
                logger.info(f"找到权威参考文本，类型: {category_ref.get('type')}")
                logger.info(f"参考文本详情: {category_ref}")
                
                # 4. 根据类型提取内容并使用大模型进行总结
                extractor = get_reference_content_extractor()
                ref_type = category_ref.get('type', 'link')
                ref_value = None
                
                if ref_type == 'pdf':
                    ref_value = category_ref.get('pdf')
                    logger.info(f"开始提取 PDF 权威文本: {ref_value}")
                elif ref_type == 'link':
                    ref_value = category_ref.get('link')
                    logger.info(f"开始提取链接权威文本: {ref_value}")
                
                # 定义三个大模型的总结函数
                async def summarize_with_doubao(content: str) -> str:
                    try:
                        return await self.doubao_service.summarize_content(content, max_length=1500)
                    except Exception as e:
                        logger.error(f"豆包总结失败: {e}")
                        return content[:1500]
                
                async def summarize_with_gemini(content: str) -> str:
                    try:
                        return await self.gemini_service.summarize_content(content, max_length=1500)
                    except Exception as e:
                        logger.error(f"Gemini总结失败: {e}")
                        return content[:1500]
                
                async def summarize_with_qwen(content: str) -> str:
                    try:
                        return await self.qwen_service.summarize_content(content, max_length=1500)
                    except Exception as e:
                        logger.error(f"Qwen总结失败: {e}")
                        return content[:1500]
                
                # 并发调用三个大模型对提取的内容进行总结
                summarize_tasks = [
                    extractor.extract_reference_content(ref_type, ref_value, 3000, summarize_with_doubao),
                    extractor.extract_reference_content(ref_type, ref_value, 3000, summarize_with_gemini),
                    extractor.extract_reference_content(ref_type, ref_value, 3000, summarize_with_qwen),
                ]
                
                summary_results = await asyncio.gather(*summarize_tasks, return_exceptions=True)
                
                # 合并三个大模型的总结结果
                summaries = []
                if isinstance(summary_results[0], str) and summary_results[0]:
                    summaries.append(f"【豆包总结】\n{summary_results[0]}")
                if isinstance(summary_results[1], str) and summary_results[1]:
                    summaries.append(f"【Gemini总结】\n{summary_results[1]}")
                if isinstance(summary_results[2], str) and summary_results[2]:
                    summaries.append(f"【Qwen总结】\n{summary_results[2]}")
                
                if summaries:
                    reference_content = "\n\n".join(summaries)
                    logger.info(f"权威参考文本提取并总结完成，总结内容长度: {len(reference_content)} 字")
                else:
                    logger.warning(f"无法提取或总结参考文本内容，类型: {ref_type}")
                    reference_content = f"参考文本类型: {ref_type}\n参考文本链接: {ref_value}"
            else:
                logger.info(f"子分类 {sub_category_id} 无权威参考文本")
                reference_content = None
        else:
            logger.warning(f"文章 {article_id} 无子分类信息")
            reference_content = None
        # 如果没有参考文本，使用默认参考提示
        if not reference_content:
            reference_content = Constants.CATEGORY_NO_AUTHORITATIVE_REFERENCE_TEXT_ERROR
        
        # 5. 构建要评价的内容
        article_content = f"""
                        标题：{article.title}
                        标签：{article.tags}
                        内容摘要（前500字）：{article.content[:500] if article.content else '无'}
                        """
        
        # 6. 异步并发调用3个大模型生成AI评论
        logger.info(f"开始并发调用3个大模型生成AI评论（基于参考文本），文章ID：{article_id}")
        
        total_start_time = time.time()
        
        async def timed_doubao_ref_call() -> Any:
            start = time.time()
            try:
                result = await self.doubao_service.with_reference_chat(article_content, reference_content)
                elapsed = time.time() - start
                logger.info(f"豆包参考文本调用完成，耗时: {elapsed:.2f}秒")
                return result
            except Exception as e:
                elapsed = time.time() - start
                logger.error(f"豆包参考文本调用失败，耗时: {elapsed:.2f}秒，错误: {e}")
                return e
        
        async def timed_gemini_ref_call() -> Any:
            start = time.time()
            try:
                result = await self.gemini_service.with_reference_chat(article_content, reference_content)
                elapsed = time.time() - start
                logger.info(f"Gemini参考文本调用完成，耗时: {elapsed:.2f}秒")
                return result
            except Exception as e:
                elapsed = time.time() - start
                logger.error(f"Gemini参考文本调用失败，耗时: {elapsed:.2f}秒，错误: {e}")
                return e
        
        async def timed_qwen_ref_call() -> Any:
            start = time.time()
            try:
                result = await self.qwen_service.with_reference_chat(article_content, reference_content)
                elapsed = time.time() - start
                logger.info(f"Qwen参考文本调用完成，耗时: {elapsed:.2f}秒")
                return result
            except Exception as e:
                elapsed = time.time() - start
                logger.error(f"Qwen参考文本调用失败，耗时: {elapsed:.2f}秒，错误: {e}")
                return e
        
        # 并发执行三个调用
        responses = await asyncio.gather(
            timed_doubao_ref_call(),
            timed_gemini_ref_call(),
            timed_qwen_ref_call(),
            return_exceptions=True
        )
        
        total_elapsed = time.time() - total_start_time
        logger.info(f"3个大模型参考文本并发调用全部完成，总耗时: {total_elapsed:.2f}秒，文章ID：{article_id}")
        
        response_doubao, response_gemini, response_qwen = responses
        
        # 检查异常返回
        if isinstance(response_doubao, Exception):
            logger.error(f"豆包参考文本最终失败: {response_doubao}")
            response_doubao = Constants.DOUBAO_CALL_FAILED_ERROR
        if isinstance(response_gemini, Exception):
            logger.error(f"Gemini参考文本最终失败: {response_gemini}")
            response_gemini = Constants.GEMINI_CALL_FAILED_ERROR
        if isinstance(response_qwen, Exception):
            logger.error(f"Qwen参考文本最终失败: {response_qwen}")
            response_qwen = Constants.QWEN_CALL_FAILED_ERROR
        
        # 7. 解析大模型返回结果
        content_doubao, star_doubao = self._parse_ai_comment_response(response_doubao)
        content_gemini, star_gemini = self._parse_ai_comment_response(response_gemini)
        content_qwen, star_qwen = self._parse_ai_comment_response(response_qwen)
        
        # 8. 构建AI评论对象
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
        
        # 9. 保存AI评论到数据库
        self.comments_mapper.create_comment_mapper(doubao_ai_comment, db)
        self.comments_mapper.create_comment_mapper(gemini_ai_comment, db)
        self.comments_mapper.create_comment_mapper(qwen_ai_comment, db)
        logger.info(f"基于参考文本的AI评论生成并保存完成，文章ID：{article_id}")

    async def generate_authority_article_with_ai_summaries(
        self, 
        reference_type: str, 
        reference_value: str
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
            logger.info(f"开始生成权威文章，类型: {reference_type}，值: {reference_value}")
            
            # 1. 提取原始内容
            extractor = get_reference_content_extractor()
            
            if reference_type.lower() == "pdf":
                raw_content = await extractor.extract_pdf_content(reference_value, max_length=3000)
            elif reference_type.lower() == "link":
                raw_content = await extractor.extract_link_content(reference_value, max_length=3000)
            else:
                logger.error(f"不支持的参考文本类型: {reference_type}")
                return {
                    "status": "error",
                    "message": f"不支持的参考文本类型: {reference_type}"
                }
            
            if not raw_content:
                logger.warning(Constants.REFERENCE_TEXT_EXTRACTION_ERROR)
                return {
                    "status": "error",
                    "message": Constants.REFERENCE_TEXT_EXTRACTION_ERROR
                }
            
            logger.info(f"原始内容提取完成，长度: {len(raw_content)} 字符")
            
            # 2. 并发调用三个大模型进行总结
            logger.info(Constants.CONCURRENT_SUMMARY_MESSAGE)
            total_start_time = time.time()
            
            async def timed_doubao_summarize() -> Optional[str]:
                start = time.time()
                try:
                    result = await self.doubao_service.summarize_content(raw_content, max_length=1500)
                    elapsed = time.time() - start
                    logger.info(f"豆包总结完成，耗时: {elapsed:.2f}秒，长度: {len(result) if result else 0}")
                    return result
                except Exception as e:
                    elapsed = time.time() - start
                    logger.error(f"豆包总结失败，耗时: {elapsed:.2f}秒，错误: {e}")
                    return None
            
            async def timed_gemini_summarize() -> Optional[str]:
                start = time.time()
                try:
                    result = await self.gemini_service.summarize_content(raw_content, max_length=1500)
                    elapsed = time.time() - start
                    logger.info(f"Gemini总结完成，耗时: {elapsed:.2f}秒，长度: {len(result) if result else 0}")
                    return result
                except Exception as e:
                    elapsed = time.time() - start
                    logger.error(f"Gemini总结失败，耗时: {elapsed:.2f}秒，错误: {e}")
                    return None
            
            async def timed_qwen_summarize() -> Optional[str]:
                start = time.time()
                try:
                    result = await self.qwen_service.summarize_content(raw_content, max_length=1500)
                    elapsed = time.time() - start
                    logger.info(f"Qwen总结完成，耗时: {elapsed:.2f}秒，长度: {len(result) if result else 0}")
                    return result
                except Exception as e:
                    elapsed = time.time() - start
                    logger.error(f"Qwen总结失败，耗时: {elapsed:.2f}秒，错误: {e}")
                    return None
            
            # 并发执行三个总结任务
            summaries = await asyncio.gather(
                timed_doubao_summarize(),
                timed_gemini_summarize(),
                timed_qwen_summarize(),
                return_exceptions=False
            )
            
            total_elapsed = time.time() - total_start_time
            logger.info(f"三个大模型总结任务全部完成，总耗时: {total_elapsed:.2f}秒")
            
            # 3. 构建返回结果
            result = {
                "status": "success",
                "reference_type": reference_type,
                "reference_value": reference_value,
                "raw_content_length": len(raw_content),
                "raw_content_preview": raw_content[:500] if raw_content else "",
                "summaries": {
                    "doubao": {
                        "content": summaries[0],
                        "length": len(summaries[0]) if summaries[0] else 0
                    },
                    "gemini": {
                        "content": summaries[1],
                        "length": len(summaries[1]) if summaries[1] else 0
                    },
                    "qwen": {
                        "content": summaries[2],
                        "length": len(summaries[2]) if summaries[2] else 0
                    }
                },
                "total_execution_time": total_elapsed
            }
            
            logger.info(Constants.CONCURRENT_CHAT_MESSAGE_SUCCESS)
            return result
            
        except Exception as e:
            logger.error(f"生成权威文章异常: {str(e)}")
            return {
                "status": "error",
                "message": f"生成权威文章失败: {str(e)}"
            }

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
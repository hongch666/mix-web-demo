from functools import lru_cache
import re
from typing import Awaitable, Callable, List, Optional
from langchain_community.document_loaders import PyPDFLoader, RecursiveUrlLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import requests
import urllib.request
from common.utils import logger

class ReferenceContentExtractor:
    """权威参考文本内容提取器"""

    # 需要过滤的噪音元素
    NOISE_PATTERNS: List[str] = [
        r'<!--.*?-->',  # HTML 注释
        r'<script.*?</script>',  # 脚本标签
        r'<style.*?</style>',  # 样式标签
        r'<nav.*?</nav>',  # 导航栏
        r'<footer.*?</footer>',  # 页脚
        r'<header.*?</header>',  # 页头
        r'<aside.*?</aside>',  # 侧边栏
        r'<advertisement.*?</advertisement>',  # 广告
        r'class=".*?ad.*?"[^>]*>.*?</[^>]*>',  # CSS 类名包含 ad 的元素
        r'class=".*?nav.*?"[^>]*>.*?</[^>]*>',  # 导航相关元素
        r'class=".*?sidebar.*?"[^>]*>.*?</[^>]*>',  # 侧边栏相关
        r'id=".*?ad.*?"[^>]*>.*?</[^>]*>',  # ID 包含 ad 的元素
        r'\s+(?:Click|Buy|Share|Like|Follow|Subscribe)\s+',  # 常见的交互词汇
        r'(?:Advertisement|广告|赞助|推广):?',  # 广告标记
        r'(?:Copyright|©|®|™)',  # 版权符号
    ]

    # 用于分割文本的分割器
    TEXT_SPLITTER: Optional[RecursiveCharacterTextSplitter] = None

    @classmethod
    def _init_text_splitter(cls) -> None:
        """初始化文本分割器"""
        if cls.TEXT_SPLITTER is None:
            try:
                cls.TEXT_SPLITTER = RecursiveCharacterTextSplitter(
                    chunk_size=1000,
                    chunk_overlap=100,
                    separators=["\n\n", "\n", " ", ""]
                )
            except Exception as e:
                logger.warning(f"初始化文本分割器失败: {e}")

    @staticmethod
    def _clean_text(text: str) -> str:
        """清理和规范化文本"""
        if not text:
            return ""

        # 移除 HTML 标签
        text = re.sub(r'<[^>]+>', '', text)

        # 应用噪音过滤模式
        for pattern in ReferenceContentExtractor.NOISE_PATTERNS:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL)

        # 规范化空白字符
        text = re.sub(r'\s+', ' ', text)

        # 移除多余的换行符
        text = re.sub(r'\n\s*\n', '\n\n', text)

        return text.strip()

    @staticmethod
    def _extract_key_points(text: str, max_length: int = 2000) -> str:
        """提取关键要点"""
        if not text:
            return ""

        # 简单的关键要点提取策略
        sentences = re.split(r'[。！？]', text)
        key_points = []

        # 优先选择包含关键词的句子
        keywords = ['定义', '概念', '原理', '方法', '步骤', '特点', '优势', '应用', '案例', '注意事项']
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            # 检查是否包含关键词
            if any(keyword in sentence for keyword in keywords):
                key_points.append(sentence)
                if len(''.join(key_points)) > max_length:
                    break

        # 如果没有找到关键词句子，按段落提取
        if not key_points:
            paragraphs = text.split('\n\n')
            for para in paragraphs[:5]:  # 取前5段
                para = para.strip()
                if para:
                    key_points.append(para)
                    if len(''.join(key_points)) > max_length:
                        break

        result = '。'.join(key_points)
        return result[:max_length] if len(result) > max_length else result

    @classmethod
    async def extract_pdf_content(cls, pdf_url: str, max_length: int = 2000) -> str:
        """从PDF URL提取内容"""
        temp_pdf_path: str = ""
        try:
            if not pdf_url:
                return ""

            logger.info(f"开始下载PDF: {pdf_url}")

            # 下载PDF到临时文件
            temp_pdf_path = f"/tmp/temp_pdf_{hash(pdf_url)}.pdf"
            urllib.request.urlretrieve(pdf_url, temp_pdf_path)

            # 使用PyPDFLoader加载PDF
            loader = PyPDFLoader(temp_pdf_path)
            documents = loader.load()

            # 提取文本内容
            full_text = ""
            for doc in documents:
                full_text += doc.page_content + "\n"

            # 清理文本
            full_text = cls._clean_text(full_text)

            # 提取关键要点
            key_points = cls._extract_key_points(full_text, max_length)

            logger.info(f"PDF内容提取完成，长度: {len(key_points)}")
            return key_points

        except Exception as e:
            logger.error(f"PDF内容提取失败: {e}")
            return ""
        finally:
            # 清理临时文件
            try:
                import os
                if temp_pdf_path and os.path.exists(temp_pdf_path):
                    os.remove(temp_pdf_path)
            except:
                pass

    @classmethod
    async def extract_link_content(cls, link_url: str, max_length: int = 2000) -> str:
        """从链接提取内容"""
        try:
            if not link_url:
                return ""

            logger.info(f"开始提取链接内容: {link_url}")

            # 使用RecursiveUrlLoader加载网页
            loader = RecursiveUrlLoader(
                url=link_url,
                max_depth=1,  # 只加载当前页面
                extractor=lambda html: cls._clean_text(html),
                prevent_outside=True,  # 防止跳转到外部链接
                use_async=True,  # 使用异步加载
                timeout=10,  # 10秒超时
            )

            documents = loader.load()

            # 提取文本内容
            full_text = ""
            for doc in documents:
                full_text += doc.page_content + "\n"

            # 清理文本
            full_text = cls._clean_text(full_text)

            # 提取关键要点
            key_points = cls._extract_key_points(full_text, max_length)

            logger.info(f"链接内容提取完成，长度: {len(key_points)}")
            return key_points

        except Exception as e:
            logger.error(f"链接内容提取失败: {e}")
            return ""

    @classmethod
    async def extract_reference_content(
        cls,
        ref_type: str,
        ref_value: str,
        max_length: int = 2000,
        summarize_func: Optional[Callable[[str], Awaitable[str]]] = None
    ) -> str:
        """提取参考内容的主入口方法"""
        try:
            if not ref_value:
                return ""

            # 根据类型提取内容
            if ref_type == 'pdf':
                raw_content = await cls.extract_pdf_content(ref_value, max_length)
            elif ref_type == 'link':
                raw_content = await cls.extract_link_content(ref_value, max_length)
            else:
                logger.warning(f"不支持的参考类型: {ref_type}")
                return ""

            if not raw_content:
                return ""

            # 如果提供了总结函数，使用AI进行总结
            if summarize_func:
                try:
                    summarized_content = await summarize_func(raw_content)
                    logger.info(f"AI总结完成，原长度: {len(raw_content)}, 总结长度: {len(summarized_content)}")
                    return summarized_content
                except Exception as e:
                    logger.warning(f"AI总结失败，使用原始内容: {e}")
                    return raw_content
            else:
                return raw_content

        except Exception as e:
            logger.error(f"参考内容提取失败: {e}")
            return ""

    @classmethod
    def extract_content_sync(cls, url: str, content_type: str = "link", max_length: int = 2000) -> str:
        """同步版本的内容提取方法"""
        try:
            if content_type == "link":
                # 同步HTTP请求
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                html_content = response.text

                # 清理文本
                text = cls._clean_text(html_content)

                # 提取关键要点
                key_points = cls._extract_key_points(text, max_length)

                return key_points
            else:
                logger.warning(f"同步模式不支持的内容类型: {content_type}")
                return ""

        except Exception as e:
            logger.error(f"同步内容提取失败: {e}")
            return ""

    @classmethod
    def split_text(cls, text: str) -> List[str]:
        """分割长文本为多个块"""
        cls._init_text_splitter()
        if cls.TEXT_SPLITTER is None:
            # 如果分割器初始化失败，直接返回原文本
            return [text] if text else []

        try:
            # 创建文档对象
            from langchain_core.documents import Document
            doc = Document(page_content=text)
            chunks = cls.TEXT_SPLITTER.split_documents([doc])
            return [chunk.page_content for chunk in chunks]
        except Exception as e:
            logger.warning(f"文本分割失败: {e}")
            return [text] if text else []

@lru_cache
def get_reference_content_extractor() -> ReferenceContentExtractor:
    """获取参考内容提取器实例"""
    ReferenceContentExtractor._init_text_splitter()
    return ReferenceContentExtractor()
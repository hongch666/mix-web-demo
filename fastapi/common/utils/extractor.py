import re
from typing import Optional, Callable, Awaitable
from langchain_community.document_loaders import PyPDFLoader, RecursiveUrlLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import requests
import urllib.request
from common.utils import fileLogger as logger

class ReferenceContentExtractor:
    """权威参考文本内容提取器"""
    
    # 需要过滤的噪音元素
    NOISE_PATTERNS = [
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
    TEXT_SPLITTER = None
    
    @classmethod
    def _init_text_splitter(cls):
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
        
        # 移除多余的空白
        text = re.sub(r'\s+', ' ', text)
        
        # 移除 HTML 标签
        text = re.sub(r'<[^>]+>', '', text)
        
        # 过滤噪音
        for pattern in ReferenceContentExtractor.NOISE_PATTERNS:
            try:
                text = re.sub(pattern, ' ', text, flags=re.IGNORECASE | re.DOTALL)
            except Exception as e:
                logger.debug(f"过滤模式 {pattern} 失败: {e}")
        
        # 移除多余的空白（再次）
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    @staticmethod
    def _extract_key_points(text: str, max_length: int = 1000) -> str:
        """
        从文本中提取关键点
        
        Args:
            text: 原始文本
            max_length: 最大返回长度
            
        Returns:
            提取的关键点，字数受限
        """
        if not text:
            return ""
        
        # 清理文本
        text = ReferenceContentExtractor._clean_text(text)
        
        # 按段落分割
        paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
        
        # 优先选择较长的段落（通常包含更多信息）
        paragraphs.sort(key=len, reverse=True)
        
        # 合并段落直到达到最大长度
        key_points = ""
        for paragraph in paragraphs:
            if len(key_points) + len(paragraph) + 1 < max_length:
                if key_points:
                    key_points += "\n" + paragraph
                else:
                    key_points = paragraph
            else:
                break
        
        # 如果仍未达到最大长度，补充单句
        if len(key_points) < max_length:
            sentences = text.split('。')
            for sentence in sentences:
                if len(key_points) + len(sentence) + 1 < max_length:
                    if key_points:
                        key_points += "。" + sentence
                    else:
                        key_points = sentence
        
        return key_points[:max_length]
    
    @staticmethod
    async def extract_pdf_content(pdf_url: str, max_length: int = 1000) -> Optional[str]:
        """
        从 PDF 链接中提取内容
        
        Args:
            pdf_url: PDF 文件的 URL 或本地路径
            max_length: 最大提取长度
            
        Returns:
            提取的关键点内容
        """
        
        try:
            logger.info(f"开始从 PDF 提取内容: {pdf_url}")
            
            # 对于 URL，需要先下载到本地
            # 这里使用 PyPDFLoader 直接加载本地或远程 PDF
            loader = PyPDFLoader(pdf_url)
            documents = loader.load()
            
            if not documents:
                logger.warning(f"无法从 PDF 加载文档: {pdf_url}")
                return None
            
            # 合并所有页面的内容
            full_text = "\n".join([doc.page_content for doc in documents])
            
            # 记录原始内容（截断到 500 字）
            original_text_preview = full_text[:500] if full_text else "（空内容）"
            logger.info(f"[PDF 原始内容] (共 {len(full_text)} 字):\n{original_text_preview}...")
            
            # 提取关键点
            key_points = ReferenceContentExtractor._extract_key_points(full_text, max_length)
            
            # 记录提取后的总结内容
            logger.info(f"[PDF 总结内容] (共 {len(key_points)} 字):\n{key_points}")
            
            logger.info(f"成功从 PDF 提取内容，原始长度: {len(full_text)} 字，总结长度: {len(key_points)} 字")
            return key_points
            
        except Exception as e:
            logger.error(f"从 PDF 提取内容失败: {str(e)}")
            return None
    
    @staticmethod
    async def extract_link_content(
        link_url: str, 
        max_length: int = 1000,
        max_depth: int = 1,
        timeout: int = 10
    ) -> Optional[str]:
        """
        从链接及其子路由中提取内容
        
        Args:
            link_url: 链接 URL
            max_length: 最大提取长度
            max_depth: 最大递归深度（获取子路由）
            timeout: 请求超时时间（秒）
            
        Returns:
            提取的关键点内容
        """
        # 优先尝试使用 RecursiveUrlLoader
        try:
            logger.info(f"使用 RecursiveUrlLoader 从链接提取内容: {link_url} (最大深度: {max_depth})")
            
            # ... existing headers ...
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
            }
            
            # 使用 RecursiveUrlLoader with custom headers
            try:
                # 尝试新版本的 RecursiveUrlLoader（支持 headers）
                loader = RecursiveUrlLoader(
                    url=link_url,
                    max_depth=max_depth,
                    timeout=timeout,
                    extractor=lambda html: ReferenceContentExtractor._clean_text(html),
                    headers=headers,
                    prevent_outside=True  # 确保不抓取域名外的链接
                )
            except TypeError:
                # 如果不支持 headers 参数，使用基础版本
                logger.debug("RecursiveUrlLoader 不支持 headers 参数，使用基础版本")
                loader = RecursiveUrlLoader(
                    url=link_url,
                    max_depth=max_depth,
                    timeout=timeout,
                    extractor=lambda html: ReferenceContentExtractor._clean_text(html),
                    prevent_outside=True
                )
            
            # 加载文档
            logger.info(f"正在递归抓取页面，这可能需要一些时间...")
            documents = loader.load()
            logger.info(f"抓取完成，共获取到 {len(documents) if documents else 0} 个页面的内容")
            
            if documents and len(documents) > 0:
                # 合并所有文档的内容
                full_text = "\n".join([doc.page_content for doc in documents if doc.page_content])
                
                if full_text.strip():
                    # 记录原始内容（截断到 500 字）
                    original_text_preview = full_text[:500] if full_text else "（空内容）"
                    logger.info(f"[链接 原始内容] (共 {len(full_text)} 字):\n{original_text_preview}...")
                    
                    # 提取关键点
                    key_points = ReferenceContentExtractor._extract_key_points(full_text, max_length)
                    
                    # 记录提取后的总结内容
                    logger.info(f"[链接 总结内容] (共 {len(key_points)} 字):\n{key_points}")
                    
                    logger.info(f"成功从链接提取内容 (RecursiveUrlLoader)，原始长度: {len(full_text)} 字，总结长度: {len(key_points)} 字，深度: {max_depth}，文档数: {len(documents)}")
                    return key_points
                else:
                    logger.warning(f"RecursiveUrlLoader 加载的文档为空: {link_url}")
            else:
                logger.warning(f"RecursiveUrlLoader 未能加载任何文档: {link_url}")
                
        except Exception as e:
            logger.warning(f"RecursiveUrlLoader 提取失败: {str(e)}，错误类型: {type(e).__name__}，尝试降级方案")
        
        # 降级处理：尝试使用 requests 库获取内容
        try:
            logger.info(f"使用 requests 库作为降级方案获取链接内容...")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            }
            
            response = requests.get(link_url, headers=headers, timeout=timeout)
            response.raise_for_status()
            
            html = response.text
            
            # 基础清理
            text = ReferenceContentExtractor._clean_text(html)
            
            if text.strip():
                # 记录原始内容（截断到 500 字）
                original_text_preview = text[:500] if text else "（空内容）"
                logger.info(f"[链接 原始内容] (共 {len(text)} 字，使用 requests):\n{original_text_preview}...")
                
                key_points = ReferenceContentExtractor._extract_key_points(text, max_length)
                
                # 记录提取后的总结内容
                logger.info(f"[链接 总结内容] (共 {len(key_points)} 字):\n{key_points}")
                
                logger.info(f"成功从链接提取内容 (requests 降级方案)，原始长度: {len(text)} 字，总结长度: {len(key_points)} 字")
                return key_points if key_points else None
            else:
                logger.warning(f"requests 获取的内容为空: {link_url}")
                return None
                
        except requests.exceptions.HTTPError as http_error:
            logger.error(f"requests 获取链接失败 - HTTP 错误: {http_error.response.status_code} {http_error}")
            return None
        except requests.exceptions.RequestException as req_error:
            logger.error(f"requests 获取链接失败: {str(req_error)}")
        except ImportError:
            logger.warning("requests 库未安装，尝试 urllib 降级方案")
        
        # 最后降级：使用 urllib
        try:
            logger.info(f"使用 urllib 作为最后降级方案获取链接内容...")
            
            req = urllib.request.Request(
                link_url,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
            )
            with urllib.request.urlopen(req, timeout=timeout) as response:
                html = response.read().decode('utf-8', errors='ignore')
                
                # 基础清理
                text = ReferenceContentExtractor._clean_text(html)
                
                if text.strip():
                    # 记录原始内容（截断到 500 字）
                    original_text_preview = text[:500] if text else "（空内容）"
                    logger.info(f"[链接 原始内容] (共 {len(text)} 字，使用 urllib):\n{original_text_preview}...")
                    
                    key_points = ReferenceContentExtractor._extract_key_points(text, max_length)
                    
                    # 记录提取后的总结内容
                    logger.info(f"[链接 总结内容] (共 {len(key_points)} 字):\n{key_points}")
                    
                    logger.info(f"成功从链接提取内容 (urllib 降级方案)，原始长度: {len(text)} 字，总结长度: {len(key_points)} 字")
                    return key_points if key_points else None
                else:
                    logger.warning(f"urllib 获取的内容为空: {link_url}")
                    return None
                
        except Exception as urllib_error:
            logger.error(f"urllib 降级方案也失败: {str(urllib_error)}")
            return None
    
    @staticmethod
    async def extract_reference_content(
        reference_type: str,
        reference_value: str,
        max_length: int = 1000,
        summarizer: Optional[Callable[[str], Awaitable[str]]] = None
    ) -> Optional[str]:
        """
        根据类型自动选择提取方法
        
        Args:
            reference_type: "link" 或 "pdf"
            reference_value: 对应的 URL 或路径
            max_length: 最大提取长度
            summarizer: 可选的总结函数，用于使用大模型对提取内容进行总结
            
        Returns:
            提取的内容（如果提供了 summarizer，则返回总结后的内容）
        """
        if not reference_value:
            return None
        
        # 先提取原始内容
        if reference_type.lower() == "pdf":
            content = await ReferenceContentExtractor.extract_pdf_content(reference_value, max_length)
        elif reference_type.lower() == "link":
            content = await ReferenceContentExtractor.extract_link_content(reference_value, max_length)
        else:
            logger.warning(f"未知的参考文本类型: {reference_type}")
            return None
        
        # 如果提供了总结函数，则调用大模型进行总结
        if content and summarizer:
            try:
                logger.info(f"开始使用大模型总结内容，原始长度: {len(content)}")
                summarized_content = await summarizer(content)
                if summarized_content:
                    logger.info(f"大模型总结完成，总结长度: {len(summarized_content)}")
                    return summarized_content
                else:
                    logger.warning("大模型总结返回空结果，使用原始提取内容")
                    return content
            except Exception as e:
                logger.error(f"大模型总结失败: {str(e)}，使用原始提取内容")
                return content
        
        return content


def get_reference_content_extractor() -> ReferenceContentExtractor:
    """获取内容提取器实例"""
    ReferenceContentExtractor._init_text_splitter()
    return ReferenceContentExtractor()

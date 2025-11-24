from typing import List, Optional
from langchain_core.tools import Tool
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores.pgvector import PGVector
from langchain_core.documents import Document
import warnings

# 抑制 PGVector 弃用警告
warnings.filterwarnings('ignore', category=DeprecationWarning)


class RAGTools:
    """RAG工具类 - 基于LangChain实现"""
    
    def __init__(self):
        """初始化RAG组件"""
        # 延迟导入避免循环依赖
        from config import load_config, load_secret_config
        from common.utils import fileLogger as logger
        
        self.logger = logger
        
        try:
            # 1. 初始化嵌入模型（通义千问）
            tongyi_cfg = load_config("tongyi") or {}
            tongyi_secret = load_secret_config("tongyi") or {}
            embedding_cfg = load_config("embedding") or {}
            
            api_key = tongyi_secret.get("api_key")
            embedding_model = embedding_cfg.get("embedding_model", "text-embedding-v3")
            self.top_k = embedding_cfg.get("top_k", 5)  # 从配置加载top_k参数
            self.similarity_threshold = embedding_cfg.get("similarity_threshold", 0.5)  # 相似度阈值（0-1之间）
            
            if not api_key:
                raise ValueError("通义千问API密钥未配置")
            
            self.embeddings = DashScopeEmbeddings(
                model=embedding_model,
                dashscope_api_key=api_key
            )
            self.logger.info(f"通义千问嵌入模型初始化成功: {embedding_model}")
            
            # 2. 初始化文本切分器
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=800,  # 每个块的大小（字符数）
                chunk_overlap=100,  # 块之间的重叠（字符数）
                length_function=len,
                separators=["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""]
            )
            self.logger.info("文本切分器初始化成功")
            
            # 3. 初始化PostgreSQL向量存储
            postgres_cfg = load_config("database")["postgres"]
            connection_string = (
                f"postgresql+psycopg2://{postgres_cfg['user']}:{postgres_cfg['password']}"
                f"@{postgres_cfg['host']}:{postgres_cfg['port']}/{postgres_cfg['database']}"
            )
            
            self.vector_store = PGVector(
                embedding_function=self.embeddings,
                collection_name="articles",
                connection_string=connection_string,
                use_jsonb=True
            )
            self.logger.info("PostgreSQL向量存储初始化成功")
            
        except Exception as e:
            self.logger.error(f"RAG工具初始化失败: {e}")
            raise
    
    def add_articles_to_vector_store(
        self, 
        article_ids: List[int],
        titles: List[str],
        contents: List[str],
        metadata_list: Optional[List[dict]] = None
    ) -> str:
        """
        将文章添加到向量存储
        
        Args:
            article_ids: 文章ID列表
            titles: 文章标题列表
            contents: 文章内容列表
            metadata_list: 元数据列表（可选）
            
        Returns:
            操作结果描述
        """
        try:
            documents = []
            
            for i, (article_id, title, content) in enumerate(zip(article_ids, titles, contents)):
                # 合并标题和内容
                full_text = f"# {title}\n\n{content}"
                
                # 切分文本
                chunks = self.text_splitter.split_text(full_text)
                
                # 为每个块创建Document对象
                for j, chunk in enumerate(chunks):
                    metadata = {
                        "article_id": article_id,
                        "title": title,
                        "chunk_index": j,
                        "total_chunks": len(chunks)
                    }
                    
                    # 添加额外的元数据
                    if metadata_list and i < len(metadata_list):
                        metadata.update(metadata_list[i])
                    
                    documents.append(Document(
                        page_content=chunk,
                        metadata=metadata
                    ))
            
            # 批量添加到向量存储
            self.vector_store.add_documents(documents)
            
            result = f"成功添加 {len(article_ids)} 篇文章，共 {len(documents)} 个文本块到向量存储"
            self.logger.info(result)
            return result
            
        except Exception as e:
            error_msg = f"添加文章到向量存储失败: {str(e)}"
            self.logger.error(error_msg)
            return error_msg
    
    def search_similar_articles(self, query: str, k: int = 5) -> str:
        """
        搜索相似文章
        
        Args:
            query: 查询文本
            k: 返回结果数量（默认使用配置中的top_k，如果传入则使用传入值）
            
        Returns:
            相似文章的文本描述
        """
        try:
            # 如果未明确传入k值，使用配置中的top_k
            search_k = k if k != 5 else self.top_k
            
            # 使用向量存储进行相似度搜索
            docs = self.vector_store.similarity_search_with_score(query, k=search_k)
            
            # 根据相似度阈值过滤结果
            filtered_docs = [(doc, score) for doc, score in docs if score >= self.similarity_threshold]
            
            if not filtered_docs:
                return "未找到相关文章。可能没有匹配的内容或相似度不足。请提供更具体的查询词或重新表述问题。"
            
            # 格式化结果
            result_text = f"找到 {len(filtered_docs)} 篇相关文章 (相似度阈值: {self.similarity_threshold}):\n\n"
            
            for i, (doc, score) in enumerate(filtered_docs, 1):
                article_id = doc.metadata.get("article_id", "未知")
                title = doc.metadata.get("title", "无标题")
                chunk_index = doc.metadata.get("chunk_index", 0)
                
                result_text += f"{i}. 文章ID: {article_id}, 标题: {title}\n"
                result_text += f"   相似度分数: {score:.4f}\n"
                result_text += f"   内容片段(第{chunk_index+1}块):\n"
                result_text += f"   {doc.page_content[:200]}...\n\n"
            
            self.logger.info(f"RAG搜索成功，返回 {len(filtered_docs)} 个结果（过滤前: {len(docs)}）")
            return result_text
            
        except Exception as e:
            error_msg = f"RAG搜索失败: {str(e)}"
            self.logger.error(error_msg)
            return error_msg
    
    def get_article_context(self, query: str, k: int = 3) -> List[Document]:
        """
        获取文章上下文（供Chain使用）
        
        Args:
            query: 查询文本
            k: 返回结果数量
            
        Returns:
            Document对象列表
        """
        try:
            docs = self.vector_store.similarity_search(query, k=k)
            self.logger.info(f"获取文章上下文成功，返回 {len(docs)} 个文档")
            return docs
        except Exception as e:
            self.logger.error(f"获取文章上下文失败: {e}")
            return []
    
    def get_langchain_tools(self) -> List[Tool]:
        """
        获取LangChain Tool对象列表
        
        Returns:
            Tool对象列表
        """
        return [
            Tool(
                name="search_articles",
                description="""使用RAG(检索增强生成)搜索相关文章。
                根据用户问题，在向量数据库中搜索最相关的文章内容。
                适用于回答关于文章内容、技术知识、教程等问题。
                参数格式: 用户的问题或关键词(字符串)
                示例: "如何使用Python进行数据分析"
                使用场景: 用户询问具体的技术问题、寻找相关文章、需要文章内容支持时使用。""",
                func=lambda query: self.search_similar_articles(query, k=self.top_k)
            )
        ]
    
    def get_retriever(self, k: int = 3):
        """
        获取LangChain检索器
        
        Args:
            k: 返回结果数量（默认使用配置中的top_k）
            
        Returns:
            VectorStoreRetriever对象
        """
        search_k = k if k != 3 else self.top_k
        return self.vector_store.as_retriever(search_kwargs={"k": search_k})


def get_rag_tools() -> RAGTools:
    """获取RAG工具实例"""
    return RAGTools()

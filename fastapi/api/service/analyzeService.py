from functools import lru_cache
from fastapi import Depends
import os
import pandas as pd
import time
from typing import Dict, List, Any
from sqlmodel import Session
from wordcloud import WordCloud
from api.mapper import ArticleMapper, get_article_mapper, UserMapper, get_user_mapper, ArticleLogMapper, get_articlelog_mapper
from config import get_db,OSSClient,load_config
from common.utils import fileLogger as logger
from common.cache import ArticleCache

class AnalyzeService:
    def __init__(self, articleMapper: ArticleMapper, articleLogMapper: ArticleLogMapper, userMapper: UserMapper):
        self.articleMapper = articleMapper
        self.articleLogMapper = articleLogMapper
        self.userMapper = userMapper
        # 初始化缓存
        self._article_cache = ArticleCache()

    def get_top10_articles_service(self, db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
        """
        获取 Top10 文章服务
        
        流程:
        1. 先尝试从缓存获取（L1本地 + L2 Redis）
        2. 缓存未命中时，按优先级查询: Hive → Spark → DB
        3. 查询成功后更新缓存
        """
        articles = None
        hive_conn = None
        data_source = None
        start = time.time()
        
        try:
            # ========== 步骤1: 尝试从缓存获取 ==========
            try:
                hive_conn = self.articleMapper.get_hive_connection()
                cached_result = self._article_cache.get(hive_conn)
                if cached_result:
                    total_time = time.time() - start
                    logger.info(f"get_top10_articles_service: [✓ 缓存命中] 耗时 {total_time:.3f}s")
                    return cached_result
            except Exception as cache_e:
                logger.debug(f"缓存获取失败，将查询数据源: {cache_e}")
            
            # ========== 步骤2: 缓存未命中，按优先级查询数据源 ==========
            logger.info("get_top10_articles_service: [✗ 缓存未命中] 开始查询数据源")
            
            # 1️⃣ 优先 Hive
            try:
                raise Exception("模拟 Hive 查询失败")
                articles = self.articleMapper.get_top10_articles_hive_mapper()
                if articles and isinstance(articles[0], dict):
                    data_source = "Hive"
                    logger.info("get_top10_articles_service: 使用 Hive 数据源")
            except Exception as hive_e:
                logger.warning(f"get_top10_articles_service: Hive 查询失败，降级为 Spark: {hive_e}")
            
            # 2️⃣ Spark 降级
            if not articles or len(articles) == 0:
                try:
                    articles = self.articleMapper.get_top10_articles_spark_mapper()
                    if articles and isinstance(articles[0], dict):
                        data_source = "Spark"
                        logger.info("get_top10_articles_service: 使用 Spark 数据源")
                except Exception as spark_e:
                    logger.error(f"get_top10_articles_service: Spark 查询失败，降级为 DB: {spark_e}")
            
            # 3️⃣ DB 兜底
            if not articles or len(articles) == 0:
                articles = self.articleMapper.get_top10_articles_db_mapper(db)
                data_source = "DB"
                logger.info("get_top10_articles_service: 使用 DB 数据源")
            
            # ========== 步骤3: 处理查询结果并更新缓存 ==========
            # 检查返回类型，如果是字典列表（Hive/Spark），直接处理
            if articles and isinstance(articles[0], dict):
                for article in articles:
                    if article.get("create_at") and hasattr(article["create_at"], 'isoformat'):
                        article["create_at"] = article["create_at"].isoformat()
                    if article.get("update_at") and hasattr(article["update_at"], 'isoformat'):
                        article["update_at"] = article["update_at"].isoformat()
                
                result = articles
            else:
                # DB 返回的是对象，需要转换为字典并关联 username
                user_ids = [article.user_id for article in articles]
                users = self.userMapper.get_users_by_ids_mapper(user_ids, db)
                user_id_to_name = {user.id: user.name for user in users}
                result = [
                    {
                        "id": article.id,
                        "title": article.title,
                        "content": article.content,
                        "user_id": article.user_id,
                        "username": user_id_to_name.get(article.user_id),
                        "tags": article.tags,
                        "status": article.status,
                        "create_at": article.create_at.isoformat() if article.create_at else None,
                        "update_at": article.update_at.isoformat() if article.update_at else None,
                        "views": article.views,
                        "sub_category_id": getattr(article, 'sub_category_id', None),
                    }
                    for article in articles
                ]
            
            # 更新缓存
            if hive_conn and result:
                try:
                    self._article_cache.set(result, hive_conn)
                    total_time = time.time() - start
                    logger.info(f"get_top10_articles_service: {data_source} 数据已更新缓存，总耗时 {total_time:.3f}s")
                except Exception as cache_e:
                    logger.warning(f"更新缓存失败: {cache_e}")
            
            return result
            
        finally:
            # 归还 Hive 连接
            if hive_conn:
                self.articleMapper.return_hive_connection(hive_conn)

    def get_keywords_dic(self) -> Dict[str, int]:
        all_keywords: List[str] = self.articleLogMapper.get_search_keywords_articlelog_mapper()
        keywords_dic: Dict[str, int] = {}
        for keyword in all_keywords:
            if keyword in keywords_dic:
                keywords_dic[keyword] += 1
            else:
                keywords_dic[keyword] = 1
        return keywords_dic

    def generate_wordcloud(self,keywords_dic: Dict[str, int]) -> None:
        if len(keywords_dic) == 0:
            logger.warning("关键词字典为空，无法生成词云图")
            raise ValueError("关键词字典为空，无法生成词云图")
        wc_config = load_config("wordcloud")
        FONT_PATH: str = wc_config["font_path"]
        WIDTH: int = wc_config["width"]
        HEIGHT: int = wc_config["height"]
        BACKGROUND_COLOR: str = wc_config["background_color"]
        wc = WordCloud(
            font_path=FONT_PATH, 
            width=WIDTH,
            height=HEIGHT,
            background_color=BACKGROUND_COLOR
        )
        wc.generate_from_frequencies(keywords_dic)
        FILE_PATH: str = load_config("files")["pic_path"]
        wc.to_file(os.path.normpath(os.path.join(os.getcwd(), FILE_PATH, "search_keywords_wordcloud.png")))
        logger.info("词云图生成成功，保存为 search_keywords_wordcloud.png")

    def upload_file(self,file_path: str, oss_path: str) -> str:
        ossClient = OSSClient()
        oss_url: str = ossClient.upload_file(
            local_file=file_path,
            oss_file=oss_path
        )
        logger.info(f"文件上传成功，OSS地址: {oss_url}")
        logger.info(f"本地文件路径: {file_path}, OSS路径: {oss_path}")
        return oss_url

    def upload_wordcloud_to_oss(self) -> str:
        FILE_PATH: str = load_config("files")["pic_path"]
        oss_url: str = self.upload_file(
            file_path=os.path.normpath(os.path.join(os.getcwd(), FILE_PATH, "search_keywords_wordcloud.png")),
            oss_path="pic/search_keywords_wordcloud.png"
        )
        return oss_url

    def export_articles_to_excel(self, db: Session = Depends(get_db)) -> str:
        FILE_PATH: str = load_config("files")["excel_path"]
        file_path = os.path.normpath(os.path.join(os.getcwd(), FILE_PATH, "articles.xlsx"))
        articles = self.articleMapper.get_all_articles_mapper(db)
        data = []
        for article in articles:
            data.append({
                "id": article.id,
                "title": article.title,
                "content": article.content,
                "user_id": article.user_id,
                "tags": article.tags,
                "status": article.status,
                "create_at": article.create_at.isoformat() if article.create_at else None,
                "update_at": article.update_at.isoformat() if article.update_at else None,
                "views": article.views,
            })
        df = pd.DataFrame(data)
        # 先写入数据
        with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, startrow=1)
            worksheet = writer.sheets['Sheet1']
            worksheet.cell(row=1, column=1, value="文章表（本表导出自系统，包含所有文章数据）")
        logger.info(f"文章表已导出到 {file_path}")
        return file_path

    def upload_excel_to_oss(self) -> str:
        FILE_PATH: str = load_config("files")["excel_path"]
        oss_url: str = self.upload_file(
            file_path=os.path.normpath(os.path.join(os.getcwd(), FILE_PATH, "articles.xlsx")),
            oss_path="excel/articles.xlsx"
        )
        return oss_url

    def get_article_statistics_service(self, db: Session = Depends(get_db)) -> Dict[str, Any]:
        """
        获取文章统计信息服务
        合并 mapper 层的4个独立方法，返回完整的统计数据
        """
        # 分别调用 mapper 层的4个方法
        total_views = self.articleMapper.get_total_views_mapper(db)
        total_articles = self.articleMapper.get_total_articles_mapper(db)
        active_authors = self.articleMapper.get_active_authors_mapper(db)
        average_views = self.articleMapper.get_average_views_mapper(db)
        
        # 组合结果
        statistics = {
            "total_views": total_views,
            "total_articles": total_articles,
            "active_authors": active_authors,
            "average_views": average_views
        }
        
        logger.info(f"获取文章统计信息: {statistics}")
        return statistics
    
@lru_cache()
def get_analyze_service(articleMapper: ArticleMapper = Depends(get_article_mapper), articleLogMapper: ArticleLogMapper = Depends(get_articlelog_mapper), userMapper: UserMapper = Depends(get_user_mapper)) -> AnalyzeService:
    return AnalyzeService(articleMapper, articleLogMapper, userMapper)
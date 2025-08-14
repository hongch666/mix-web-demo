from fastapi import Depends
import os
import pandas as pd
from typing import Dict, List, Any

from sqlmodel import Session

from api.mapper import (
    get_all_articles_mapper,
    get_top10_articles_hive_mapper,
    get_top10_articles_spark_mapper,
    get_top10_articles_db_mapper,
    get_users_by_ids_mapper,
    get_search_keywords_articlelog_mapper
)
from config import get_db,OSSClient,load_config
from common.utils import fileLogger as logger
from wordcloud import WordCloud

def get_top10_articles_service(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    articles = None
    # 1. 优先 Hive
    try:
        articles = get_top10_articles_hive_mapper()
        if articles and isinstance(articles[0], dict):
            logger.info("get_top10_articles_service: 使用 Hive 数据源")
    except Exception as hive_e:
        logger.warning(f"get_top10_articles_service: Hive 获取失败，降级为 Spark: {hive_e}")
    # 2. Spark 降级
    if not articles or len(articles) == 0:
        try:
            articles = get_top10_articles_spark_mapper()
            if articles and isinstance(articles[0], dict):
                logger.info("get_top10_articles_service: 使用 Spark 数据源")
        except Exception as spark_e:
            logger.error(f"get_top10_articles_service: Spark 获取失败，降级为 DB: {spark_e}")
    # 3. DB 兜底
    if not articles or len(articles) == 0:
        articles = get_top10_articles_db_mapper(db)
        logger.info("get_top10_articles_service: 使用 DB 数据源")

    # 检查返回类型，如果是字典列表（csv/spark/hive），直接返回（已带username字段）
    if articles and isinstance(articles[0], dict):
        for article in articles:
            if article.get("create_at") and hasattr(article["create_at"], 'isoformat'):
                article["create_at"] = article["create_at"].isoformat()
            if article.get("update_at") and hasattr(article["update_at"], 'isoformat'):
                article["update_at"] = article["update_at"].isoformat()
        return articles
    else:
        # 兜底db查询，仍需查user表
        user_ids = [article.user_id for article in articles]
        users = get_users_by_ids_mapper(user_ids, db)
        user_id_to_name = {user.id: user.name for user in users}
        return [
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

def get_keywords_dic() -> Dict[str, int]:
    all_keywords: List[str] = get_search_keywords_articlelog_mapper()
    keywords_dic: Dict[str, int] = {}
    for keyword in all_keywords:
        if keyword in keywords_dic:
            keywords_dic[keyword] += 1
        else:
            keywords_dic[keyword] = 1
    return keywords_dic

def generate_wordcloud(keywords_dic: Dict[str, int]) -> None:
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

def upload_file(file_path: str, oss_path: str) -> str:
    ossClient = OSSClient()
    oss_url: str = ossClient.upload_file(
        local_file=file_path,
        oss_file=oss_path
    )
    logger.info(f"文件上传成功，OSS地址: {oss_url}")
    logger.info(f"本地文件路径: {file_path}, OSS路径: {oss_path}")
    return oss_url

def upload_wordcloud_to_oss() -> str:
    FILE_PATH: str = load_config("files")["pic_path"]
    oss_url: str = upload_file(
        file_path=os.path.normpath(os.path.join(os.getcwd(), FILE_PATH, "search_keywords_wordcloud.png")),
        oss_path="pic/search_keywords_wordcloud.png"
    )
    return oss_url

def export_articles_to_excel(db: Session = Depends(get_db)) -> str:
    FILE_PATH: str = load_config("files")["excel_path"]
    file_path = os.path.normpath(os.path.join(os.getcwd(), FILE_PATH, "articles.xlsx"))
    articles = get_all_articles_mapper(db)
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

def upload_excel_to_oss() -> str:
    FILE_PATH: str = load_config("files")["excel_path"]
    oss_url: str = upload_file(
        file_path=os.path.normpath(os.path.join(os.getcwd(), FILE_PATH, "articles.xlsx")),
        oss_path="excel/articles.xlsx"
    )
    return oss_url
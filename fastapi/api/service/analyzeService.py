from sqlalchemy.orm import Session
from fastapi import Depends
import os
import pandas as pd
from typing import Dict, List, Any

from api.mapper.articleMapper import get_all_articles_mapper,get_top10_articles_mapper
from api.mapper.userMapper import get_users_by_ids_mapper
from api.mapper.articlelogMapper import get_search_keywords_articlelog_mapper
from config.mysql import get_db
from common.utils.writeLog import fileLogger as logger
from wordcloud import WordCloud
from config.oss import OSSClient
from config.config import load_config

def get_top10_articles_service(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    articles = get_top10_articles_mapper(db)
    # 获取所有作者id
    user_ids = [article.user_id for article in articles]
    # 批量查user表
    users = get_users_by_ids_mapper(user_ids, db)
    user_id_to_name = {user.id: user.name for user in users}
    # 转换为字典并加上username
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
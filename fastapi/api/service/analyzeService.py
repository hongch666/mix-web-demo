from fastapi import Depends
import os
import pandas as pd
from typing import Dict, List, Any

from sqlmodel import Session

from api.mapper import get_all_articles_mapper,get_top10_articles_mapper,get_users_by_ids_mapper,get_search_keywords_articlelog_mapper
from config import OSSClient,load_config
from common.utils import fileLogger as logger
from wordcloud import WordCloud

async def get_top10_articles_service() -> List[Dict[str, Any]]:
    articles = await get_top10_articles_mapper()
    # 检查返回类型，如果是字典列表则直接处理，如果是Article对象则按原逻辑处理
    if articles and isinstance(articles[0], dict):
        # 新的字典格式，直接获取user_ids并补充username
        user_ids = [article["user_id"] for article in articles if article.get("user_id")]
        users = get_users_by_ids_mapper(user_ids)
        user_id_to_name = {user.id: user.name for user in users}
        
        # 为每个字典添加username字段
        for article in articles:
            article["username"] = user_id_to_name.get(article.get("user_id"))
            # 确保时间格式正确
            if article.get("create_at") and hasattr(article["create_at"], 'isoformat'):
                article["create_at"] = article["create_at"].isoformat()
            if article.get("update_at") and hasattr(article["update_at"], 'isoformat'):
                article["update_at"] = article["update_at"].isoformat()
        
        return articles
    else:
        # 原有的Article对象格式
        user_ids = [article.user_id for article in articles]
        users = get_users_by_ids_mapper(user_ids)
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

async def get_keywords_dic() -> Dict[str, int]:
    all_keywords: List[str] = await get_search_keywords_articlelog_mapper()
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

async def export_articles_to_excel() -> str:
    FILE_PATH: str = load_config("files")["excel_path"]
    file_path = os.path.normpath(os.path.join(os.getcwd(), FILE_PATH, "articles.xlsx"))
    articles = await get_all_articles_mapper()
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
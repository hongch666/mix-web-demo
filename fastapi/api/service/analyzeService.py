from sqlalchemy.orm import Session
from fastapi import Depends
import os
from typing import Dict, List, Any

from config.mysql import get_db
from entity.po.article import Article
from config.mongodb import db as mongo_db
from common.utils.writeLog import fileLogger as logger
from wordcloud import WordCloud
from config.oss import OSSClient
from config.config import load_config

def get_top10_articles_service(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    articles = db.query(Article).limit(10).all()
    # 转换为字典
    return [
        {
            "id": article.id,
            "title": article.title,
            "content": article.content,
            "user_id": article.user_id,
            "tags": article.tags,
            "status": article.status,
            "create_at": article.create_at.isoformat() if article.create_at else None,
            "update_at": article.update_at.isoformat() if article.update_at else None,
            "views": article.views,
        }
        for article in articles
    ]

def get_keywords_dic() -> Dict[str, int]:
    logs = mongo_db["articlelogs"]
    cursor = logs.find({"action": "search"})
    all_keywords: List[str] = []
    for log in cursor:
        content: Dict[str, Any] = log.get('content', {})
        if 'Keyword' in content:
            if content['Keyword'] == "":
                continue
            all_keywords.append(content['Keyword'])
    keywords_dic: Dict[str, int] = {}
    for keyword in all_keywords:
        if keyword in keywords_dic:
            keywords_dic[keyword] += 1
        else:
            keywords_dic[keyword] = 1
    return keywords_dic

def generate_wordcloud(keywords_dic: Dict[str, int]) -> None:
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

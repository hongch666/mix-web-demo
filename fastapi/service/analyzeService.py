from sqlalchemy.orm import Session
from fastapi import Depends

from config.mysql import get_db
from entity.po.article import Article
from config.mongodb import db as mongo_db
from common.utils.logger import logger
from wordcloud import WordCloud
from config.oss import OSSClient
from config.config import load_config

def get_top10_articles_service(db: Session = Depends(get_db)):
    articles = db.query(Article).order_by(Article.views.desc()).limit(10).all()
    return articles

def get_keywords_dic():
    logs = mongo_db["articlelogs"]
    cursor = logs.find({"action": "search"})
    all_keywords = []
    for log in cursor:
        content = log.get('content', {})
        if 'Keyword' in content:
            if content['Keyword'] == "":
                continue
            all_keywords.append(content['Keyword'])
    keywords_dic = {}
    for keyword in all_keywords:
        if keyword in keywords_dic:
            keywords_dic[keyword] += 1
        else:
            keywords_dic[keyword] = 1
    return keywords_dic

def generate_wordcloud(keywords_dic):
    wc_config = load_config("wordcloud")
    FONT_PATH = wc_config["font_path"]
    WIDTH = wc_config["width"]
    HEIGHT = wc_config["height"]
    BACKGROUND_COLOR = wc_config["background_color"]
    wc = WordCloud(
        font_path=FONT_PATH, 
        width=WIDTH,
        height=HEIGHT,
        background_color=BACKGROUND_COLOR
    )
    wc.generate_from_frequencies(keywords_dic)
    wc.to_file("fastapi/static/pic/search_keywords_wordcloud.png")
    logger.info("词云图生成成功，保存为 search_keywords_wordcloud.png")

def upload_file(file_path: str, oss_path: str):
    ossClient = OSSClient()
    oss_url = ossClient.upload_file(
        local_file=file_path,
        oss_file=oss_path
    )
    logger.info(f"文件上传成功，OSS地址: {oss_url}")
    return oss_url

def upload_wordcloud_to_oss():
    oss_url = upload_file(
        file_path="fastapi/static/pic/search_keywords_wordcloud.png",
        oss_path="pic/search_keywords_wordcloud.png"
    )
    return oss_url

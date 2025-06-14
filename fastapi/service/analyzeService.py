import logging
from sqlalchemy.orm import Session
from fastapi import Depends

from config.mysql import get_db
from po.article import Article
from config.mongodb import db as mongo_db
from config.logger import logger
from wordcloud import WordCloud
from config.oss import OSSClient

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
    wc = WordCloud(
        font_path="/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", 
        width=800,
        height=400,
        background_color="white"
    )
    wc.generate_from_frequencies(keywords_dic)
    wc.to_file("fastapi/pic/search_keywords_wordcloud.png")
    logger.info("词云图生成成功，保存为 search_keywords_wordcloud.png")

def upload_file(file_path: str, file_name: str):
    ossClient = OSSClient()
    oss_url = ossClient.upload_file(
        local_file=file_path,
        oss_file=file_name
    )
    logger.info(f"文件上传成功，OSS地址: {oss_url}")
    return oss_url

def upload_wordcloud_to_oss():
    oss_url = upload_file(
        file_path="fastapi/pic/search_keywords_wordcloud.png",
        file_name="search_keywords_wordcloud.png"
    )
    return oss_url
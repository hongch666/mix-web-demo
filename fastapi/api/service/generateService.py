import jieba.analyse
import re

def extract_tags(text: str, topK: int = 5) -> str:
    """
    提取文本中的关键词作为tags
    :param text: 文章内容
    :param topK: 返回关键词数量
    :return: 关键词列表
    """
    # 去除markdown格式符号
    text = re.sub(r'(```[\s\S]*?```|`[^`]*`|\!\[[^\]]*\]\([^\)]*\)|\[[^\]]*\]\([^\)]*\)|[#>*_~\-\+\=\[\]`]|\d+\.|\n)', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    tags: list[str] = jieba.analyse.extract_tags(text, topK=topK)
    return ",".join(tags)

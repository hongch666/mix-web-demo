import jieba.analyse

def extract_tags(text, topK=5):
    """
    提取文本中的关键词作为tags
    :param text: 文章内容
    :param topK: 返回关键词数量
    :return: 关键词列表
    """
    tags = jieba.analyse.extract_tags(text, topK=topK)
    return ",".join(tags)


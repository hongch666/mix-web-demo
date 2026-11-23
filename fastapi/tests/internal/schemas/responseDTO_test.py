"""用户分析响应模型的单元测试"""

from app.internal.schemas import ArticleViewDistributionResponse


# 数仓 Mapper 与 NestJS 远端都以 views 字段返回单篇阅读量，响应模型必须按该键解析
def test_article_view_distribution_parses_views_key() -> None:
    response = ArticleViewDistributionResponse.model_validate(
        {
            "total_views": 10,
            "articles": [{"article_id": 7091, "title": "编程入门", "views": 9}],
        }
    )

    assert response.total_views == 10
    assert response.articles[0].article_id == 7091
    assert response.articles[0].views == 9

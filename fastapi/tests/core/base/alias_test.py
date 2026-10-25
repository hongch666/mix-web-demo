"""字段别名工具的单元测试"""

from typing import Optional

from pydantic import BaseModel

from app.core.base import Alias, to_snake


class SampleDTO(BaseModel):
    """测试用 DTO，覆盖驼峰字段的别名校验与序列化"""

    model_config = {"populate_by_name": True}

    userId: Optional[int] = Alias("userId", default=None, description="用户ID")
    articleIds: list[int] = Alias(
        "articleIds", default_factory=list, description="文章ID列表"
    )


# 驼峰字段名按大写字符边界转换为蛇形
def test_to_snake_converts_camel_boundaries() -> None:
    assert to_snake("userId") == "user_id"
    assert to_snake("articleIds") == "article_ids"
    assert to_snake("streamFormat") == "stream_format"


# 蛇形别名是默认的校验名
def test_alias_accepts_snake_alias_on_validation() -> None:
    sample: SampleDTO = SampleDTO(user_id=7, article_ids=[1, 2])

    assert sample.userId == 7
    assert sample.articleIds == [1, 2]


# 开启 populate_by_name 后驼峰原名同样可用于校验
def test_alias_accepts_camel_field_name_when_populate_by_name() -> None:
    sample: SampleDTO = SampleDTO(userId=8, articleIds=[3])

    assert sample.userId == 8
    assert sample.articleIds == [3]


# 序列化统一输出蛇形字段名
def test_alias_serializes_to_snake_keys() -> None:
    sample: SampleDTO = SampleDTO(userId=8, articleIds=[3])

    assert sample.model_dump(by_alias=True) == {"user_id": 8, "article_ids": [3]}

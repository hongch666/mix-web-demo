"""生成请求参数的单元测试"""

import pytest
from pydantic import ValidationError

from app.internal.schemas import GenerateDTO


# 空白文本被 text 校验器拒绝
def test_generate_dto_rejects_blank_text() -> None:
    with pytest.raises(ValidationError) as error:
        GenerateDTO(text="   ")

    assert error.value.errors()[0]["type"] == "text_empty"

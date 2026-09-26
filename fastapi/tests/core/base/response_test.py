from app.core.base.response import ApiResponse, error, success
from app.core.constants import HttpCode


# success 默认返回 200 状态码与 success 消息并携带数据
def test_success_response_defaults_and_payload() -> None:
    response = success({"id": 1})

    assert isinstance(response, ApiResponse)
    assert response.code == HttpCode.OK
    assert response.data == {"id": 1}
    assert response.msg == "success"


# success 支持自定义消息且缺省数据为 None
def test_success_response_custom_message_and_none_data() -> None:
    response = success(msg="created")

    assert response.code == HttpCode.OK
    assert response.data is None
    assert response.msg == "created"


# error 保留传入的状态码、消息与数据
def test_error_response_preserves_code_message_and_data() -> None:
    response = error(code=HttpCode.BAD_REQUEST, msg="invalid", data={"field": "name"})

    assert response.code == HttpCode.BAD_REQUEST
    assert response.msg == "invalid"
    assert response.data == {"field": "name"}

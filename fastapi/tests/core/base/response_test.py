from app.core.base.response import ApiResponse, error, success
from app.core.constants import HttpCode


def test_success_response_defaults_and_payload() -> None:
    response = success({"id": 1})

    assert isinstance(response, ApiResponse)
    assert response.code == HttpCode.OK
    assert response.data == {"id": 1}
    assert response.msg == "success"


def test_success_response_custom_message_and_none_data() -> None:
    response = success(msg="created")

    assert response.code == HttpCode.OK
    assert response.data is None
    assert response.msg == "created"


def test_error_response_preserves_code_message_and_data() -> None:
    response = error(code=HttpCode.BAD_REQUEST, msg="invalid", data={"field": "name"})

    assert response.code == HttpCode.BAD_REQUEST
    assert response.msg == "invalid"
    assert response.data == {"field": "name"}

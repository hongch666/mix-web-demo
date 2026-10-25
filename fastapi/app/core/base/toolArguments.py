import json
from typing import Annotated, Any

from pydantic import BeforeValidator


def parse_json_string(value: Any) -> Any:
    """把模型写成 JSON 字符串的容器参数还原成列表或字典

    模型偶尔会把整个对象或数组拼成一个字符串再传参（例如把 pipeline 写成
    "[{\\"$match\\": {}}]"），解析失败或类型不符时原样返回，交给字段校验报出可读错误
    """
    if not isinstance(value, str):
        return value

    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return value


# 工具入参中的键值对象与数组统一使用这两个类型，容忍 JSON 字符串写法
JsonObjectArgument = Annotated[dict[str, Any], BeforeValidator(parse_json_string)]
JsonArrayArgument = Annotated[list[Any], BeforeValidator(parse_json_string)]

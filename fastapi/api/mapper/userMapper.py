from sqlmodel import Session, select

from common.client import call_remote_service
from entity.po import User

async def get_users_by_ids_mapper(user_ids: list[int]) -> list[User]:
    # 使用Spring部分获取日志数据
    result = await call_remote_service(
        service_name="spring",
        path=f"/users/batch/{','.join(map(str, user_ids))}",
        method="GET"
    )

    return result["data"]["list"]

async def get_all_users_mapper() -> list[User]:
    # 使用Spring部分获取日志数据
    result = await call_remote_service(
        service_name="spring",
        path="/users",
        method="GET"
    )
    
    return result["data"]["list"]
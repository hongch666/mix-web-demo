from functools import lru_cache

from common.client import call_remote_service
from entity.po import User

class UserMapper:

    async def get_users_by_ids_mapper(self, user_ids: list[int]) -> list[User]:
        # 使用Spring部分获取用户数据
        result = await call_remote_service(
            service_name="spring",
            path=f"/users/batch/{','.join(map(str, user_ids))}",
            method="GET"
        )

        return result["data"]["list"]
    
@lru_cache()
def get_user_mapper() -> UserMapper:
    return UserMapper()
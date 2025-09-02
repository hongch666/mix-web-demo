from functools import lru_cache

from common.client import call_remote_service
from entity.po import User

class UserMapper:

    async def get_all_users_mapper(self) -> list[User]:
        # 使用Spring部分获取日志数据
        result = await call_remote_service(
            service_name="spring",
            path="/users",
            method="GET"
        )
        
        return result["data"]["list"]
    
@lru_cache()
def get_user_mapper() -> UserMapper:
    return UserMapper()
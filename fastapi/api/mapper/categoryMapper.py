from functools import lru_cache
from common.client import call_remote_service
from entity.po import Category

class CategoryMapper:

    async def get_all_categories_mapper(self) -> list[Category]:
        # 使用Spring部分获取日志数据
        result = await call_remote_service(
            service_name="spring",
            path="/category/all",
            method="GET"
        )

        return result["data"]["list"]

@lru_cache()
def get_category_mapper() -> CategoryMapper:
    return CategoryMapper()
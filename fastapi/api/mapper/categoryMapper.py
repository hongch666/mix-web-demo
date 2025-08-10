from sqlmodel import Session, select
from common.client import call_remote_service
from entity.po import Category

async def get_all_categories_mapper() -> list[Category]:
    # 使用Spring部分获取日志数据
    result = await call_remote_service(
        service_name="spring",
        path="/category/all",
        method="GET"
    )

    return result["data"]["list"]
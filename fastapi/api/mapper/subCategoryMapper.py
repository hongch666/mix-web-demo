from sqlmodel import Session, select

from common.client import call_remote_service
from entity.po import SubCategory

async def get_all_subcategories_mapper() -> list[SubCategory]:
    # 使用Spring部分获取日志数据
    result = await call_remote_service(
        service_name="spring",
        path=f"/category/sub/all",
        method="GET"
    )
    return result["data"]["list"]
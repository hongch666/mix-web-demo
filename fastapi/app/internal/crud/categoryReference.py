from functools import lru_cache
from typing import Any, Dict, Optional

from app.core.base import Logger
from app.core.constants import Messages
from app.internal.models import CategoryReference
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class CategoryReferenceMapper:
    """权威参考文本 Mapper - 直接从数据库查询"""

    async def _get_category_reference_by_sub_category_id_mapper_sync(
        self, sub_category_id: int, db: AsyncSession
    ) -> Optional[Dict[str, Any]]:
        """
        根据子分类ID获取权威参考文本
        """

        Logger.info(Messages.CATEGORY_REFERENCE_QUERY_STARTED(sub_category_id))

        statement = select(CategoryReference).where(
            CategoryReference.sub_category_id == sub_category_id
        )
        category_ref = (await db.execute(statement)).scalars().first()

        if category_ref:
            Logger.info(Messages.CATEGORY_REFERENCE_FOUND(category_ref.type))
            return {
                "id": category_ref.id,
                "sub_category_id": category_ref.sub_category_id,
                "type": category_ref.type,
                "link": category_ref.link,
                "pdf": category_ref.pdf,
            }
        else:
            Logger.info(Messages.CATEGORY_REFERENCE_NOT_FOUND(sub_category_id))
            return None

    async def get_category_reference_by_sub_category_id_mapper_async(
        self, sub_category_id: int, db: AsyncSession
    ) -> Optional[Dict[str, Any]]:
        return await self._get_category_reference_by_sub_category_id_mapper_sync(
            sub_category_id, db
        )


@lru_cache()
def get_category_reference_mapper() -> CategoryReferenceMapper:
    """获取 CategoryReferenceMapper 实例"""
    return CategoryReferenceMapper()

from functools import lru_cache
from typing import Dict, List

from app.internal.models import Category, SubCategory
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class CategoryMapper:
    """分类 Mapper"""

    async def _get_all_categories_mapper_sync(self, db: AsyncSession) -> List[Category]:
        statement = select(Category).distinct()
        return (await db.execute(statement)).scalars().all()

    async def _get_subcategories_with_parent_mapper_sync(
        self, db: AsyncSession
    ) -> List[Dict[str, object]]:
        """
        获取所有子分类及其对应的父分类名称
        返回: [{"id": 1, "name": "Python", "category_name": "编程语言", ...}, ...]
        """
        subcategories = (await db.execute(select(SubCategory))).scalars().all()

        result: List[Dict[str, object]] = []
        for sub in subcategories:
            # 获取对应的父分类
            parent = (
                await db.execute(select(Category).where(Category.id == sub.category_id))
                .scalars()
                .first()
            )
            result.append(
                {
                    "id": sub.id,
                    "name": sub.name,
                    "category_id": sub.category_id,
                    "category_name": parent.name if parent else "未分类",
                    "create_time": sub.create_time.isoformat()
                    if sub.create_time
                    else None,
                    "update_time": sub.update_time.isoformat()
                    if sub.update_time
                    else None,
                }
            )

        return result

    async def get_all_categories_mapper_async(self, db: AsyncSession) -> List[Category]:
        return await self._get_all_categories_mapper_sync(db)

    async def get_subcategories_with_parent_mapper_async(
        self, db: AsyncSession
    ) -> List[Dict[str, object]]:
        return await self._get_subcategories_with_parent_mapper_sync(db)


@lru_cache()
def get_category_mapper() -> CategoryMapper:
    return CategoryMapper()

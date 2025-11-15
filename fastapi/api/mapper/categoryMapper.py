from functools import lru_cache
from sqlmodel import Session, select
from entity.po import Category, SubCategory

class CategoryMapper:

    def get_all_categories_mapper(self, db: Session) -> list[Category]:
        statement = select(Category).distinct()
        return db.exec(statement).all()
    
    def get_subcategories_with_parent_mapper(self, db: Session) -> list[dict]:
        """
        获取所有子分类及其对应的父分类名称
        返回: [{"id": 1, "name": "Python", "category_name": "编程语言", ...}, ...]
        """
        subcategories = db.exec(select(SubCategory)).all()
        
        result = []
        for sub in subcategories:
            # 获取对应的父分类
            parent = db.exec(select(Category).where(Category.id == sub.category_id)).first()
            result.append({
                "id": sub.id,
                "name": sub.name,
                "category_id": sub.category_id,
                "category_name": parent.name if parent else "未分类",
                "create_time": sub.create_time.isoformat() if sub.create_time else None,
                "update_time": sub.update_time.isoformat() if sub.update_time else None,
            })
        
        return result
    
@lru_cache()
def get_category_mapper() -> CategoryMapper:
    return CategoryMapper()
from functools import lru_cache
from typing import Optional, Dict, Any
from sqlmodel import Session, select
from entity.po import CategoryReference
from common.utils import fileLogger as logger

class CategoryReferenceMapper:
    """权威参考文本 Mapper - 直接从数据库查询"""

    def get_category_reference_by_sub_category_id_mapper(
        self, 
        sub_category_id: int,
        db: Session
    ) -> Optional[Dict[str, Any]]:
        """
        根据子分类ID获取权威参考文本
        
        Returns: {
            "id": 1,
            "sub_category_id": 1,
            "type": "link" | "pdf",
            "link": "https://...",
            "pdf": "https://..."
        }
        """
        
        logger.info(f"获取子分类 {sub_category_id} 的权威参考文本")
        
        statement = select(CategoryReference).where(
            CategoryReference.sub_category_id == sub_category_id
        )
        category_ref = db.exec(statement).first()
        
        if category_ref:
            logger.info(f"成功获取参考文本: type={category_ref.type}")
            return {
                "id": category_ref.id,
                "sub_category_id": category_ref.sub_category_id,
                "type": category_ref.type,
                "link": category_ref.link,
                "pdf": category_ref.pdf
            }
        else:
            logger.info(f"子分类 {sub_category_id} 无权威参考文本")
            return None
                


@lru_cache()
def get_category_reference_mapper() -> CategoryReferenceMapper:
    """获取 CategoryReferenceMapper 实例"""
    return CategoryReferenceMapper()

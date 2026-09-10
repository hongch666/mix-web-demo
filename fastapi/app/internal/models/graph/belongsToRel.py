from neomodel import AsyncStructuredRel


class BelongsToRel(AsyncStructuredRel):
    """Article -[:BELONGS_TO]-> SubCategory 与 SubCategory -[:BELONGS_TO]-> Category 关系（无属性）"""

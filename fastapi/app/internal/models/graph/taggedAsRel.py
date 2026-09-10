from neomodel import AsyncStructuredRel


class TaggedAsRel(AsyncStructuredRel):
    """Article -[:TAGGED_AS]-> Tag 关系（无属性）"""

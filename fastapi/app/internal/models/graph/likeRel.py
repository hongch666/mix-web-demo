from neomodel import AsyncStructuredRel, StringProperty


class LikeRel(AsyncStructuredRel):
    """User -[:LIKES]-> Article 关系属性"""

    created_at = StringProperty(db_property="createdAt")

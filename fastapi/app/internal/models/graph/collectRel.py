from neomodel import AsyncStructuredRel, StringProperty


class CollectRel(AsyncStructuredRel):
    """User -[:COLLECTS]-> Article 关系属性"""

    created_at = StringProperty(db_property="createdAt")

from neomodel import AsyncStructuredRel, StringProperty


class FollowRel(AsyncStructuredRel):
    """User -[:FOLLOWS]-> User 关系属性"""

    created_at = StringProperty(db_property="createdAt")

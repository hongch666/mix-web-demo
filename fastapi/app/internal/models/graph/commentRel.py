from neomodel import AsyncStructuredRel, IntegerProperty, StringProperty


class CommentRel(AsyncStructuredRel):
    """User -[:COMMENTED_ON]-> Article 关系属性"""

    comment_id = IntegerProperty(db_property="commentId")
    created_at = StringProperty(db_property="createdAt")

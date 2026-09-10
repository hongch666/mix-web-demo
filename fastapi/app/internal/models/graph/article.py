from neomodel import (
    AsyncRelationshipFrom,
    AsyncRelationshipTo,
    AsyncStructuredNode,
    IntegerProperty,
    StringProperty,
)

from .belongsToRel import BelongsToRel
from .collectRel import CollectRel
from .commentRel import CommentRel
from .likeRel import LikeRel
from .publishedByRel import PublishedByRel
from .taggedAsRel import TaggedAsRel


class Article(AsyncStructuredNode):
    """文章节点"""

    graph_id = IntegerProperty(db_property="id", unique_index=True)
    title = StringProperty()
    tags = StringProperty()
    status = StringProperty()
    views = IntegerProperty()
    create_at = StringProperty(db_property="createAt")
    update_at = StringProperty(db_property="updateAt")
    content_hash = StringProperty(db_property="contentHash")
    updated_at = StringProperty(db_property="updatedAt")

    author = AsyncRelationshipTo(
        "app.internal.models.graph.user.User",
        "PUBLISHED_BY",
        model=PublishedByRel,
    )
    sub_category = AsyncRelationshipTo(
        "app.internal.models.graph.subCategory.SubCategory",
        "BELONGS_TO",
        model=BelongsToRel,
    )
    tags_rel = AsyncRelationshipTo(
        "app.internal.models.graph.tag.Tag", "TAGGED_AS", model=TaggedAsRel
    )
    liked_by = AsyncRelationshipFrom(
        "app.internal.models.graph.user.User", "LIKES", model=LikeRel
    )
    collected_by = AsyncRelationshipFrom(
        "app.internal.models.graph.user.User", "COLLECTS", model=CollectRel
    )
    commented_by = AsyncRelationshipFrom(
        "app.internal.models.graph.user.User", "COMMENTED_ON", model=CommentRel
    )

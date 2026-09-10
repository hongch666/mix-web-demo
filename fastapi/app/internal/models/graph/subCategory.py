from neomodel import (
    AsyncRelationshipFrom,
    AsyncRelationshipTo,
    AsyncStructuredNode,
    IntegerProperty,
    StringProperty,
)

from .belongsToRel import BelongsToRel


class SubCategory(AsyncStructuredNode):
    """子分类节点"""

    graph_id = IntegerProperty(db_property="id", unique_index=True)
    name = StringProperty()
    category_id = IntegerProperty(db_property="categoryId")
    updated_at = StringProperty(db_property="updatedAt")

    category = AsyncRelationshipTo(
        "app.internal.models.graph.category.Category",
        "BELONGS_TO",
        model=BelongsToRel,
    )
    articles = AsyncRelationshipFrom(
        "app.internal.models.graph.article.Article",
        "BELONGS_TO",
        model=BelongsToRel,
    )

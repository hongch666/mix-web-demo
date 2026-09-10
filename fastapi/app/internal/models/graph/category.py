from neomodel import (
    AsyncRelationshipFrom,
    AsyncStructuredNode,
    IntegerProperty,
    StringProperty,
)

from .belongsToRel import BelongsToRel


class Category(AsyncStructuredNode):
    """主分类节点"""

    graph_id = IntegerProperty(db_property="id", unique_index=True)
    name = StringProperty()
    updated_at = StringProperty(db_property="updatedAt")

    sub_categories = AsyncRelationshipFrom(
        "app.internal.models.graph.subCategory.SubCategory",
        "BELONGS_TO",
        model=BelongsToRel,
    )

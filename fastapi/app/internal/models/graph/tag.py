from neomodel import AsyncRelationshipFrom, AsyncStructuredNode, StringProperty

from .taggedAsRel import TaggedAsRel


class Tag(AsyncStructuredNode):
    """标签节点"""

    name = StringProperty(unique_index=True)

    articles = AsyncRelationshipFrom(
        "app.internal.models.graph.article.Article",
        "TAGGED_AS",
        model=TaggedAsRel,
    )

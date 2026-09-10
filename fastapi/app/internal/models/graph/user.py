from neomodel import (
    AsyncRelationshipFrom,
    AsyncRelationshipTo,
    AsyncStructuredNode,
    IntegerProperty,
    StringProperty,
)

from .collectRel import CollectRel
from .commentRel import CommentRel
from .followRel import FollowRel
from .likeRel import LikeRel
from .publishedByRel import PublishedByRel


class User(AsyncStructuredNode):
    """用户节点

    关联的目标类若不在本模块内，必须写成「模块路径.类名」的全名：
    neomodel 按声明关系时所在的模块去解析类名，跨模块只写类名会解析失败
    """

    graph_id = IntegerProperty(db_property="id", unique_index=True)
    name = StringProperty()
    email = StringProperty()
    role = StringProperty()
    img = StringProperty()
    signature = StringProperty()
    created_at = StringProperty(db_property="createdAt")
    updated_at = StringProperty(db_property="updatedAt")

    published_articles = AsyncRelationshipFrom(
        "app.internal.models.graph.article.Article",
        "PUBLISHED_BY",
        model=PublishedByRel,
    )
    liked_articles = AsyncRelationshipTo(
        "app.internal.models.graph.article.Article", "LIKES", model=LikeRel
    )
    collected_articles = AsyncRelationshipTo(
        "app.internal.models.graph.article.Article", "COLLECTS", model=CollectRel
    )
    commented_articles = AsyncRelationshipTo(
        "app.internal.models.graph.article.Article", "COMMENTED_ON", model=CommentRel
    )
    # 自身关联，类名在本模块内，可直接用短名
    following = AsyncRelationshipTo("User", "FOLLOWS", model=FollowRel)
    followers = AsyncRelationshipFrom("User", "FOLLOWS", model=FollowRel)

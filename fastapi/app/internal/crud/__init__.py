from typing import List

from .aiHistory import AiHistoryMapper, get_ai_history_mapper
from .article import ArticleMapper, get_article_mapper
from .category import CategoryMapper, get_category_mapper
from .categoryReference import CategoryReferenceMapper, get_category_reference_mapper
from .collect import CollectMapper, get_collect_mapper
from .comments import CommentsMapper, get_comments_mapper
from .focus import FocusMapper, get_focus_mapper
from .like import LikeMapper, get_like_mapper
from .user import UserMapper, get_user_mapper

__all__: List[str] = [
    "get_article_mapper",
    "ArticleMapper",
    "get_category_mapper",
    "CategoryMapper",
    "get_user_mapper",
    "UserMapper",
    "get_ai_history_mapper",
    "AiHistoryMapper",
    "CommentsMapper",
    "get_comments_mapper",
    "LikeMapper",
    "get_like_mapper",
    "CollectMapper",
    "get_collect_mapper",
    "FocusMapper",
    "get_focus_mapper",
    "CategoryReferenceMapper",
    "get_category_reference_mapper",
]

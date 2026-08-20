from typing import Any, Dict, List, Optional

from app.core.client import call_remote_service


class SpringClient:
    """Spring 服务客户端，提供 MySQL 数据查询能力"""

    SERVICE_NAME: str = "spring"

    async def get_articles_by_ids(self, ids: List[int]) -> List[Dict[str, Any]]:
        """批量查询文章"""
        if not ids:
            return []
        result: Dict[str, Any] = await call_remote_service(
            service_name=self.SERVICE_NAME,
            path="/articles/batch",
            method="POST",
            json={"ids": ids},
        )
        return result.get("data", [])

    async def get_article_views_by_ids(self, ids: List[int]) -> Dict[int, int]:
        """批量查询文章阅读量"""
        if not ids:
            return {}
        result: Dict[str, Any] = await call_remote_service(
            service_name=self.SERVICE_NAME,
            path="/articles/views/batch",
            method="POST",
            json={"ids": ids},
        )
        return result.get("data", {})

    async def get_users_by_ids(self, ids: List[int]) -> List[Dict[str, Any]]:
        """批量查询用户"""
        if not ids:
            return []
        result: Dict[str, Any] = await call_remote_service(
            service_name=self.SERVICE_NAME,
            path="/users/batch",
            method="POST",
            json={"ids": ids},
        )
        return result.get("data", [])

    async def get_comment_scores_by_article_ids(
        self, ids: List[int]
    ) -> Dict[int, Dict[str, Any]]:
        """批量查询评论评分（按角色分组）"""
        if not ids:
            return {}
        result: Dict[str, Any] = await call_remote_service(
            service_name=self.SERVICE_NAME,
            path="/comments/scores/batch",
            method="POST",
            json={"ids": ids},
        )
        return result.get("data", {})

    async def get_like_counts_by_article_ids(self, ids: List[int]) -> Dict[int, int]:
        """批量查询点赞数"""
        if not ids:
            return {}
        result: Dict[str, Any] = await call_remote_service(
            service_name=self.SERVICE_NAME,
            path="/likes/counts/batch",
            method="POST",
            json={"ids": ids},
        )
        return result.get("data", {})

    async def get_collect_counts_by_article_ids(self, ids: List[int]) -> Dict[int, int]:
        """批量查询收藏数"""
        if not ids:
            return {}
        result: Dict[str, Any] = await call_remote_service(
            service_name=self.SERVICE_NAME,
            path="/collects/counts/batch",
            method="POST",
            json={"ids": ids},
        )
        return result.get("data", {})

    async def get_follow_counts_by_user_ids(self, ids: List[int]) -> Dict[int, int]:
        """批量查询粉丝数"""
        if not ids:
            return {}
        result: Dict[str, Any] = await call_remote_service(
            service_name=self.SERVICE_NAME,
            path="/focus/counts/batch",
            method="POST",
            json={"ids": ids},
        )
        return result.get("data", {})

    async def get_categories_by_ids(self, ids: List[int]) -> List[Dict[str, Any]]:
        """批量查询分类"""
        if not ids:
            return []
        result: Dict[str, Any] = await call_remote_service(
            service_name=self.SERVICE_NAME,
            path="/category/batch",
            method="POST",
            json={"ids": ids},
        )
        return result.get("data", [])

    async def get_sub_categories_by_ids(self, ids: List[int]) -> List[Dict[str, Any]]:
        """批量查询子分类"""
        if not ids:
            return []
        result: Dict[str, Any] = await call_remote_service(
            service_name=self.SERVICE_NAME,
            path="/category/sub/batch",
            method="POST",
            json={"ids": ids},
        )
        return result.get("data", [])

    async def get_all_categories(self) -> List[Dict[str, Any]]:
        """获取所有分类"""
        result: Dict[str, Any] = await call_remote_service(
            service_name=self.SERVICE_NAME,
            path="/category/internal/all",
            method="GET",
        )
        return result.get("data", [])

    async def get_subcategories_with_parent(self) -> List[Dict[str, Any]]:
        """获取所有子分类及对应的父分类信息"""
        result: Dict[str, Any] = await call_remote_service(
            service_name=self.SERVICE_NAME,
            path="/category/internal/sub/with-parent",
            method="GET",
        )
        return result.get("data", [])

    async def get_category_reference_by_sub_category_id(
        self, sub_category_id: int
    ) -> Optional[Dict[str, Any]]:
        """根据子分类ID获取权威参考文本"""
        result: Dict[str, Any] = await call_remote_service(
            service_name=self.SERVICE_NAME,
            path=f"/category/reference/sub/{sub_category_id}",
            method="GET",
        )
        return result.get("data")

    async def get_published_articles(
        self, page: int = 1, size: int = 10
    ) -> Dict[str, Any]:
        """分页获取已发布文章列表"""
        result: Dict[str, Any] = await call_remote_service(
            service_name=self.SERVICE_NAME,
            path="/articles/list",
            method="GET",
            params={"page": page, "size": size},
        )
        return result.get("data", {"total": 0, "records": []})

    # ==================== 统计接口 ====================

    async def get_total_views(self) -> int:
        """获取所有文章的总阅读量"""
        result: Dict[str, Any] = await call_remote_service(
            service_name=self.SERVICE_NAME,
            path="/articles/statistics/total-views",
            method="GET",
        )
        return result.get("data", 0)

    async def get_total_articles(self) -> int:
        """获取文章总数"""
        result: Dict[str, Any] = await call_remote_service(
            service_name=self.SERVICE_NAME,
            path="/articles/statistics/total",
            method="GET",
        )
        return result.get("data", 0)

    async def get_active_authors(self) -> int:
        """获取活跃作者数"""
        result: Dict[str, Any] = await call_remote_service(
            service_name=self.SERVICE_NAME,
            path="/articles/statistics/active-authors",
            method="GET",
        )
        return result.get("data", 0)

    async def get_average_views(self) -> float:
        """获取平均阅读次数"""
        result: Dict[str, Any] = await call_remote_service(
            service_name=self.SERVICE_NAME,
            path="/articles/statistics/average-views",
            method="GET",
        )
        return result.get("data", 0.0)

    async def get_articles_for_excel_export(self) -> List[Dict[str, Any]]:
        """获取导出Excel所需文章数据"""
        result: Dict[str, Any] = await call_remote_service(
            service_name=self.SERVICE_NAME,
            path="/articles/statistics/excel-export",
            method="GET",
        )
        return result.get("data", [])

    async def get_top10_articles(self) -> List[Dict[str, Any]]:
        """获取Top10文章（按阅读量降序）"""
        result: Dict[str, Any] = await call_remote_service(
            service_name=self.SERVICE_NAME,
            path="/articles/statistics/top10",
            method="GET",
        )
        return result.get("data", [])

    async def get_category_article_count(self) -> List[Dict[str, Any]]:
        """获取按子分类统计的文章数量"""
        result: Dict[str, Any] = await call_remote_service(
            service_name=self.SERVICE_NAME,
            path="/articles/statistics/category-count",
            method="GET",
        )
        return result.get("data", [])

    async def get_monthly_publish_count(self) -> List[Dict[str, Any]]:
        """获取最近24个月文章发布数量统计"""
        result: Dict[str, Any] = await call_remote_service(
            service_name=self.SERVICE_NAME,
            path="/articles/statistics/monthly-publish-count",
            method="GET",
        )
        return result.get("data", [])

    # ==================== 点赞统计接口 ====================

    async def get_total_likes(self) -> int:
        """获取所有文章的总点赞数"""
        result: Dict[str, Any] = await call_remote_service(
            service_name=self.SERVICE_NAME,
            path="/likes/statistics/total",
            method="GET",
        )
        return result.get("data", 0)

    async def get_average_likes(self) -> float:
        """获取每篇文章的平均点赞数"""
        result: Dict[str, Any] = await call_remote_service(
            service_name=self.SERVICE_NAME,
            path="/likes/statistics/average",
            method="GET",
        )
        return result.get("data", 0.0)

    async def get_monthly_like_trend(self, user_id: int) -> Dict[str, Any]:
        """获取用户本月点赞的趋势"""
        result: Dict[str, Any] = await call_remote_service(
            service_name=self.SERVICE_NAME,
            path=f"/likes/statistics/monthly-trend/{user_id}",
            method="GET",
        )
        return result.get("data", {"total": 0, "daily_trends": []})

    # ==================== 收藏统计接口 ====================

    async def get_total_collects(self) -> int:
        """获取所有文章的总收藏数"""
        result: Dict[str, Any] = await call_remote_service(
            service_name=self.SERVICE_NAME,
            path="/collects/statistics/total",
            method="GET",
        )
        return result.get("data", 0)

    async def get_average_collects(self) -> float:
        """获取每篇文章的平均收藏数"""
        result: Dict[str, Any] = await call_remote_service(
            service_name=self.SERVICE_NAME,
            path="/collects/statistics/average",
            method="GET",
        )
        return result.get("data", 0.0)

    async def get_monthly_collect_trend(self, user_id: int) -> Dict[str, Any]:
        """获取用户本月收藏的趋势"""
        result: Dict[str, Any] = await call_remote_service(
            service_name=self.SERVICE_NAME,
            path=f"/collects/statistics/monthly-trend/{user_id}",
            method="GET",
        )
        return result.get("data", {"total": 0, "daily_trends": []})

    # ==================== 关注统计接口 ====================

    async def get_followers_in_period(
        self, user_id: int, start_date: str, end_date: str
    ) -> int:
        """获取指定时间段内的新增粉丝数"""
        result: Dict[str, Any] = await call_remote_service(
            service_name=self.SERVICE_NAME,
            path=f"/focus/statistics/followers-in-period/{user_id}",
            method="GET",
            params={"startDate": start_date, "endDate": end_date},
        )
        return result.get("data", 0)

    async def get_daily_follows(
        self, user_id: int, start_date: str, end_date: str
    ) -> Dict[str, Any]:
        """获取指定时间段内每天的关注数"""
        result: Dict[str, Any] = await call_remote_service(
            service_name=self.SERVICE_NAME,
            path=f"/focus/statistics/daily-follows/{user_id}",
            method="GET",
            params={"startDate": start_date, "endDate": end_date},
        )
        return result.get("data", {"daily_follows": []})

    async def get_total_follows(self, user_id: int) -> int:
        """获取用户的总关注数"""
        result: Dict[str, Any] = await call_remote_service(
            service_name=self.SERVICE_NAME,
            path=f"/focus/statistics/total-follows/{user_id}",
            method="GET",
        )
        return result.get("data", 0)

    async def get_monthly_follow_trend(self, user_id: int) -> Dict[str, Any]:
        """获取用户本月关注的趋势"""
        result: Dict[str, Any] = await call_remote_service(
            service_name=self.SERVICE_NAME,
            path=f"/focus/statistics/monthly-trend/{user_id}",
            method="GET",
        )
        return result.get("data", {"total": 0, "daily_trends": []})

    # ==================== 评论统计接口 ====================

    async def get_ai_comments_num_by_article_id(self, article_id: int) -> int:
        """获取文章的AI评论数"""
        result: Dict[str, Any] = await call_remote_service(
            service_name=self.SERVICE_NAME,
            path=f"/comments/statistics/ai-count/{article_id}",
            method="GET",
        )
        return result.get("data", 0)

    async def delete_ai_comments_by_article_id(self, article_id: int) -> None:
        """删除文章的AI评论"""
        await call_remote_service(
            service_name=self.SERVICE_NAME,
            path=f"/comments/statistics/delete-ai/{article_id}",
            method="POST",
        )

    async def get_monthly_comment_trend(self, user_id: int) -> Dict[str, Any]:
        """获取用户本月评论的趋势"""
        result: Dict[str, Any] = await call_remote_service(
            service_name=self.SERVICE_NAME,
            path=f"/comments/statistics/monthly-trend/{user_id}",
            method="GET",
        )
        return result.get("data", {"total": 0, "daily_trends": []})

    # ==================== 评论操作接口 ====================

    async def create_comment(self, comment_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建评论"""
        result: Dict[str, Any] = await call_remote_service(
            service_name=self.SERVICE_NAME,
            path="/comments/internal/create",
            method="POST",
            json=comment_data,
        )
        return result.get("data", {})

    async def get_neo4j_sync_users(
        self, updated_after: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """获取用户表数据用于Neo4j同步"""
        params = {"updatedAfter": updated_after} if updated_after else None
        result: Dict[str, Any] = await call_remote_service(
            service_name=self.SERVICE_NAME,
            path="/users/neo4j-sync",
            method="GET",
            params=params,
        )
        return result.get("data", [])

    async def get_neo4j_sync_categories(
        self, updated_after: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """获取分类表数据用于Neo4j同步"""
        params = {"updatedAfter": updated_after} if updated_after else None
        result: Dict[str, Any] = await call_remote_service(
            service_name=self.SERVICE_NAME,
            path="/category/internal/neo4j-sync",
            method="GET",
            params=params,
        )
        return result.get("data", [])

    async def get_neo4j_sync_sub_categories(
        self, updated_after: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """获取子分类表数据用于Neo4j同步"""
        params = {"updatedAfter": updated_after} if updated_after else None
        result: Dict[str, Any] = await call_remote_service(
            service_name=self.SERVICE_NAME,
            path="/category/internal/sub/neo4j-sync",
            method="GET",
            params=params,
        )
        return result.get("data", [])

    async def get_neo4j_sync_articles(
        self, updated_after: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """获取文章表数据用于Neo4j同步"""
        params = {"updatedAfter": updated_after} if updated_after else None
        result: Dict[str, Any] = await call_remote_service(
            service_name=self.SERVICE_NAME,
            path="/articles/neo4j-sync",
            method="GET",
            params=params,
        )
        return result.get("data", [])

    async def get_neo4j_sync_likes(
        self, updated_after: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """获取点赞表数据用于Neo4j同步"""
        params = {"updatedAfter": updated_after} if updated_after else None
        result: Dict[str, Any] = await call_remote_service(
            service_name=self.SERVICE_NAME,
            path="/likes/neo4j-sync",
            method="GET",
            params=params,
        )
        return result.get("data", [])

    async def get_neo4j_sync_collects(
        self, updated_after: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """获取收藏表数据用于Neo4j同步"""
        params = {"updatedAfter": updated_after} if updated_after else None
        result: Dict[str, Any] = await call_remote_service(
            service_name=self.SERVICE_NAME,
            path="/collects/neo4j-sync",
            method="GET",
            params=params,
        )
        return result.get("data", [])

    async def get_neo4j_sync_comments(
        self, updated_after: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """获取评论表数据用于Neo4j同步"""
        params = {"updatedAfter": updated_after} if updated_after else None
        result: Dict[str, Any] = await call_remote_service(
            service_name=self.SERVICE_NAME,
            path="/comments/neo4j-sync",
            method="GET",
            params=params,
        )
        return result.get("data", [])

    async def get_neo4j_sync_focus(
        self, updated_after: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """获取关注表数据用于Neo4j同步"""
        params = {"updatedAfter": updated_after} if updated_after else None
        result: Dict[str, Any] = await call_remote_service(
            service_name=self.SERVICE_NAME,
            path="/focus/neo4j-sync",
            method="GET",
            params=params,
        )
        return result.get("data", [])

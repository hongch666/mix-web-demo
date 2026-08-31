from datetime import datetime
from typing import Final


class WarehouseScripts:
    """ClickHouse 数仓同步和汇总 SQL"""

    PLATFORM_STATS_QUERY: Final[str] = (
        "SELECT total_views, total_articles, active_authors, average_views, "
        "total_likes, average_likes, total_collects, average_collects "
        "FROM warehouse.ads_platform_stats FINAL ORDER BY stat_time DESC LIMIT 1"
    )

    ODS_ARTICLE_LOG_TABLE: Final[str] = "ods_article_log"
    ODS_ARTICLE_LOG_INSERT: Final[str] = (
        "INSERT INTO warehouse.ods_article_log "
        "(event_id, user_id, article_id, action, content, created_at) VALUES"
    )

    BATCH_SIZE: Final[int] = 1000
    EPOCH_WATERMARK: Final[str] = "1970-01-01 00:00:00"
    EPOCH_DATETIME: Final[datetime] = datetime(1970, 1, 1)
    REMOTE_SOURCES: Final[tuple[tuple[str, str, tuple[str, ...]], ...]] = (
        ("ods_articles", "articles", ("id", "title", "user_id", "sub_category_id", "tags", "status", "views", "create_at", "update_at")),
        ("ods_user", "user", ("id", "name", "role", "img", "signature", "create_at", "update_at")),
        ("ods_category", "category", ("id", "name", "create_time", "update_time")),
        ("ods_sub_category", "sub_category", ("id", "name", "category_id", "create_time", "update_time")),
        ("ods_likes", "likes", ("id", "article_id", "user_id", "created_time")),
        ("ods_collects", "collects", ("id", "article_id", "user_id", "created_time")),
        ("ods_comments", "comments", ("id", "user_id", "article_id", "star", "create_time", "update_time")),
        ("ods_focus", "focus", ("id", "user_id", "focus_id", "created_time")),
    )
    DATETIME_COLUMNS: Final[frozenset[str]] = frozenset(
        {"create_at", "update_at", "create_time", "update_time", "created_time"}
    )
    STRING_COLUMNS: Final[frozenset[str]] = frozenset(
        {"tags", "role", "img", "signature", "title", "name"}
    )
    INTEGER_COLUMNS: Final[frozenset[str]] = frozenset(
        {"status", "views", "star", "id", "user_id", "article_id", "sub_category_id", "category_id", "focus_id"}
    )

    WATERMARK_SELECT: Final[str] = (
        "SELECT last_watermark FROM warehouse.sync_watermark FINAL "
        "WHERE table_name = %(table_name)s LIMIT 1"
    )
    WATERMARK_UPSERT: Final[str] = (
        "INSERT INTO warehouse.sync_watermark (table_name, last_watermark, updated_at) VALUES"
    )

    REFRESH_DERIVED_TABLES: Final[tuple[str, ...]] = (
        "TRUNCATE TABLE warehouse.dim_user",
        "TRUNCATE TABLE warehouse.dim_category",
        "TRUNCATE TABLE warehouse.dwd_article_event",
        "TRUNCATE TABLE warehouse.dwd_user_action",
        "TRUNCATE TABLE warehouse.dws_article_day",
        "TRUNCATE TABLE warehouse.dws_user_day",
        "TRUNCATE TABLE warehouse.ads_top10_articles",
        "TRUNCATE TABLE warehouse.ads_category_stats",
        "TRUNCATE TABLE warehouse.ads_monthly_publish",
        "TRUNCATE TABLE warehouse.ads_platform_stats",
        "TRUNCATE TABLE warehouse.ads_user_profile",
    )

    REFRESH_DIM_USER: Final[str] = """
        INSERT INTO warehouse.dim_user
        SELECT id, name, role, img, signature, create_at, update_at
        FROM warehouse.ods_user FINAL
    """
    REFRESH_DIM_CATEGORY: Final[str] = """
        INSERT INTO warehouse.dim_category
        SELECT sc.id, sc.name, sc.category_id, ifNull(c.name, ''), sc.update_time
        FROM warehouse.ods_sub_category AS sc FINAL
        LEFT JOIN warehouse.ods_category AS c FINAL ON sc.category_id = c.id
    """
    REFRESH_DWD_ARTICLE: Final[str] = """
        INSERT INTO warehouse.dwd_article_event
        SELECT a.id, a.title, a.user_id, a.views, a.status,
               a.sub_category_id, ifNull(d.parent_category_id, 0),
               ifNull(d.parent_category_name, ''), toDate(a.create_at),
               a.create_at, a.update_at
        FROM warehouse.ods_articles AS a FINAL
        LEFT JOIN warehouse.dim_category AS d FINAL ON a.sub_category_id = d.sub_category_id
        WHERE a.status = 1
    """
    REFRESH_DWD_ACTION: Final[str] = """
        INSERT INTO warehouse.dwd_user_action
        SELECT concat('like:', toString(id)), 'likes', id, 'like', user_id,
               article_id, toDate(created_time), created_time FROM warehouse.ods_likes FINAL
        UNION ALL
        SELECT concat('collect:', toString(id)), 'collects', id, 'collect', user_id,
               article_id, toDate(created_time), created_time FROM warehouse.ods_collects FINAL
        UNION ALL
        SELECT concat('comment:', toString(id)), 'comments', id, 'comment', user_id,
               article_id, toDate(create_time), create_time FROM warehouse.ods_comments FINAL
        UNION ALL
        SELECT concat('focus:', toString(id)), 'focus', id, 'focus', user_id,
               focus_id, toDate(created_time), created_time FROM warehouse.ods_focus FINAL
        UNION ALL
        SELECT event_id, 'article_log', 0, action, user_id, article_id,
               toDate(created_at), created_at FROM warehouse.ods_article_log FINAL
    """
    REFRESH_DWS_ARTICLE: Final[str] = """
        INSERT INTO warehouse.dws_article_day
        SELECT a.create_date, a.id, a.user_id, a.parent_category_id, a.views,
               ifNull(x.like_count, 0), ifNull(x.collect_count, 0),
               ifNull(x.comment_count, 0)
        FROM warehouse.dwd_article_event AS a FINAL
        LEFT JOIN
        (
            SELECT action_date, article_id,
                   countIf(action_type = 'like') AS like_count,
                   countIf(action_type = 'collect') AS collect_count,
                   countIf(action_type = 'comment') AS comment_count
            FROM warehouse.dwd_user_action FINAL
            WHERE article_id > 0
            GROUP BY action_date, article_id
        ) AS x ON a.create_date = x.action_date AND a.id = x.article_id
    """
    REFRESH_DWS_USER: Final[str] = """
        INSERT INTO warehouse.dws_user_day
        SELECT action_date, user_id,
               countIf(action_type = 'like'), countIf(action_type = 'collect'),
               countIf(action_type = 'comment'), countIf(action_type = 'focus'),
               uniqExactIf(article_id, action_type = 'like'), max(action_time)
        FROM warehouse.dwd_user_action FINAL
        GROUP BY action_date, user_id
    """
    REFRESH_ADS: Final[tuple[str, ...]] = (
        """
        INSERT INTO warehouse.ads_top10_articles
        SELECT id, title, '', status, views, create_at, update_at, user_id,
               sub_category_id, now()
        FROM warehouse.dwd_article_event FINAL ORDER BY views DESC LIMIT 10
        """,
        """
        INSERT INTO warehouse.ads_category_stats
        SELECT parent_category_id, any(parent_category_name), count(), now()
        FROM warehouse.dwd_article_event FINAL GROUP BY parent_category_id
        """,
        """
        INSERT INTO warehouse.ads_monthly_publish
        SELECT formatDateTime(create_at, '%Y-%m'), count(), now()
        FROM warehouse.dwd_article_event FINAL
        WHERE create_at >= subtractMonths(now(), 24)
        GROUP BY formatDateTime(create_at, '%Y-%m')
        """,
        """
        INSERT INTO warehouse.ads_platform_stats
        SELECT 1, now(), sum(views), count(), uniqExact(user_id), avg(views),
               (SELECT count() FROM warehouse.dwd_user_action FINAL WHERE action_type = 'like'),
               if(count() = 0, 0, (SELECT count() FROM warehouse.dwd_user_action FINAL WHERE action_type = 'like') / count()),
               (SELECT count() FROM warehouse.dwd_user_action FINAL WHERE action_type = 'collect'),
               if(count() = 0, 0, (SELECT count() FROM warehouse.dwd_user_action FINAL WHERE action_type = 'collect') / count())
        FROM warehouse.dwd_article_event FINAL
        """,
        """
        INSERT INTO warehouse.ads_user_profile
        SELECT u.id, u.name,
               countIf(a.action_type = 'like'), countIf(a.action_type = 'collect'),
               countIf(a.action_type = 'comment'), countIf(a.action_type = 'focus'),
               ifNull(p.total_articles, 0), ifNull(p.total_views, 0),
               ifNull(max(a.action_time), toDateTime('1970-01-01 00:00:00')), now()
        FROM warehouse.dim_user AS u FINAL
        LEFT JOIN warehouse.dwd_user_action AS a FINAL ON u.id = a.user_id
        LEFT JOIN
        (
            SELECT user_id, count() AS total_articles, sum(views) AS total_views
            FROM warehouse.dwd_article_event FINAL GROUP BY user_id
        ) AS p ON u.id = p.user_id
        GROUP BY u.id, u.name, p.total_articles, p.total_views
        """,
    )

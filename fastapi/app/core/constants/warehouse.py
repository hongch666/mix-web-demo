from datetime import datetime
from typing import Final


class WarehouseScripts:
    """ClickHouse 数仓同步和汇总 SQL"""

    PLATFORM_STATS_QUERY: Final[str] = (
        "SELECT total_views, total_articles, active_authors, average_views, "
        "total_likes, average_likes, total_collects, average_collects "
        "FROM warehouse.ads_platform_stats FINAL ORDER BY stat_time DESC LIMIT 1"
    )

    USER_FOLLOWERS_BY_DAY_QUERY: Final[str] = """
        SELECT stat_date, focus_count
        FROM warehouse.ads_user_day FINAL
        WHERE user_id = %(user_id)s
          AND stat_date >= %(start_date)s AND stat_date < %(end_date)s
        ORDER BY stat_date
    """
    USER_VIEW_DISTRIBUTION_QUERY: Final[str] = """
        SELECT article_id, article_title, view_count
        FROM warehouse.ads_user_view_articles FINAL
        WHERE user_id = %(user_id)s AND article_id > 0
        ORDER BY view_count DESC
    """
    USER_TOTAL_FOLLOWS_QUERY: Final[str] = (
        "SELECT total_followers FROM warehouse.ads_user_stats FINAL "
        "WHERE user_id = %(user_id)s"
    )
    USER_PROFILE_QUERY: Final[str] = """
        SELECT s.user_id, ifNull(u.name, ''), s.total_articles,
               s.total_views_received, s.total_likes_received,
               s.total_collects_received, s.total_followers,
               s.total_likes_given, s.total_collects_given,
               s.total_comments, s.total_focus, s.last_active_time
        FROM warehouse.ads_user_stats AS s FINAL
        LEFT JOIN warehouse.dim_user AS u FINAL ON s.user_id = u.id
        WHERE s.user_id = %(user_id)s
    """
    USER_DAILY_FOLLOW_QUERY: Final[str] = """
        SELECT stat_date, focus_count
        FROM warehouse.ads_user_day FINAL
        WHERE user_id = %(user_id)s
          AND stat_date >= %(start_date)s AND stat_date < %(end_date)s
        ORDER BY stat_date
    """
    USER_MONTHLY_ACTION_QUERY: Final[str] = """
        SELECT stat_date, %(metric)s
        FROM warehouse.ads_user_day FINAL
        WHERE user_id = %(user_id)s
          AND stat_date >= %(start_date)s AND stat_date < %(end_date)s
        ORDER BY stat_date
    """

    ODS_ARTICLE_LOG_TABLE: Final[str] = "ods_article_log"
    ODS_ARTICLE_LOG_INSERT: Final[str] = (
        "INSERT INTO warehouse.ods_article_log "
        "(event_id, user_id, article_id, action, content, created_at) VALUES"
    )

    BATCH_SIZE: Final[int] = 1000
    ARTICLE_LOG_BATCH_SIZE: Final[int] = 5000
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
        {"status", "views", "id", "user_id", "article_id", "sub_category_id", "category_id", "focus_id"}
    )
    FLOAT_COLUMNS: Final[frozenset[str]] = frozenset({"star"})

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
        "TRUNCATE TABLE warehouse.ads_user_day",
        "TRUNCATE TABLE warehouse.ads_user_view_articles",
        "TRUNCATE TABLE warehouse.ads_user_stats",
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
        -- 主数据源：MongoDB 事件流（12 类行为，含 view 与 unlike 等负信号）
        SELECT event_id, 'article_log', 0, action, user_id, article_id,
               toDate(created_at), created_at FROM warehouse.ods_article_log FINAL
        UNION ALL
        -- 补充数据源：仅取事件流起点之前的关系表存量，避免与事件流重复计数
        SELECT concat('like:', toString(id)), 'likes', id, 'like', user_id,
               article_id, toDate(created_time), created_time FROM warehouse.ods_likes FINAL
        WHERE created_time < (SELECT ifNull(min(created_at), toDateTime('1970-01-01 00:00:00')) FROM warehouse.ods_article_log)
        UNION ALL
        SELECT concat('collect:', toString(id)), 'collects', id, 'collect', user_id,
               article_id, toDate(created_time), created_time FROM warehouse.ods_collects FINAL
        WHERE created_time < (SELECT ifNull(min(created_at), toDateTime('1970-01-01 00:00:00')) FROM warehouse.ods_article_log)
        UNION ALL
        SELECT concat('comment:', toString(id)), 'comments', id, 'comment', user_id,
               article_id, toDate(create_time), create_time FROM warehouse.ods_comments FINAL
        WHERE create_time < (SELECT ifNull(min(created_at), toDateTime('1970-01-01 00:00:00')) FROM warehouse.ods_article_log)
        UNION ALL
        SELECT concat('focus:', toString(id)), 'focus', id, 'focus', user_id,
               focus_id, toDate(created_time), created_time FROM warehouse.ods_focus FINAL
        WHERE created_time < (SELECT ifNull(min(created_at), toDateTime('1970-01-01 00:00:00')) FROM warehouse.ods_article_log)
    """
    REFRESH_DWS_ARTICLE: Final[str] = """
        INSERT INTO warehouse.dws_article_day
        -- 行为按日聚合为主驱动（不依赖文章发布日），文章维度 LEFT JOIN 补齐
        -- views 为文章当前累计浏览量冗余；每日新增浏览由 view_count 列体现
        SELECT
            x.stat_date,
            x.article_id,
            ifNull(a.user_id, 0) AS user_id,
            ifNull(a.parent_category_id, 0) AS parent_category_id,
            ifNull(a.views, 0) AS views,
            x.like_count,
            x.collect_count,
            x.comment_count,
            x.view_count
        FROM
        (
            SELECT action_date AS stat_date, article_id,
                   countIf(action_type = 'like') AS like_count,
                   countIf(action_type = 'collect') AS collect_count,
                   countIf(action_type = 'comment') AS comment_count,
                   countIf(action_type = 'view') AS view_count
            FROM warehouse.dwd_user_action FINAL
            WHERE article_id > 0
            GROUP BY action_date, article_id
        ) AS x
        LEFT JOIN warehouse.dwd_article_event AS a FINAL ON x.article_id = a.id
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
    )

    # 用户分析 ADS 层刷新：日粒度行为汇总（含作为观众的行为）
    REFRESH_ADS_USER_DAY: Final[str] = """
        INSERT INTO warehouse.ads_user_day
        SELECT action_date, user_id,
               countIf(action_type = 'like'), countIf(action_type = 'collect'),
               countIf(action_type = 'comment'), countIf(action_type = 'focus'),
               countIf(action_type = 'view'), max(action_time), now()
        FROM warehouse.dwd_user_action FINAL
        GROUP BY action_date, user_id
    """

    # 用户分析 ADS 层刷新：用户浏览的文章分布（预聚合浏览事件，消除查询期 JOIN）
    REFRESH_ADS_USER_VIEW_ARTICLES: Final[str] = """
        INSERT INTO warehouse.ads_user_view_articles
        SELECT v.user_id, v.article_id, ifNull(a.title, ''), v.view_count, now()
        FROM
        (
            SELECT user_id, article_id, count() AS view_count
            FROM warehouse.dwd_user_action FINAL
            WHERE action_type = 'view' AND article_id > 0
            GROUP BY user_id, article_id
        ) AS v
        LEFT JOIN warehouse.dwd_article_event AS a FINAL ON v.article_id = a.id
    """

    # 用户分析 ADS 层刷新：用户累计指标（作为观众的主动行为 + 作为作者的被动数据）
    REFRESH_ADS_USER_STATS: Final[str] = """
        INSERT INTO warehouse.ads_user_stats
        SELECT
            u.id AS user_id,
            ifNull(g.total_likes_given, 0),
            ifNull(g.total_collects_given, 0),
            ifNull(g.total_comments, 0),
            ifNull(g.total_focus, 0),
            ifNull(g.total_views_given, 0),
            ifNull(p.total_articles, 0),
            ifNull(p.total_views_received, 0),
            ifNull(p.total_likes_received, 0),
            ifNull(p.total_collects_received, 0),
            ifNull(f.total_followers, 0),
            ifNull(g.last_active_time, toDateTime('1970-01-01 00:00:00')),
            now()
        FROM warehouse.dim_user AS u FINAL
        LEFT JOIN
        (
            SELECT user_id,
                   countIf(action_type = 'like') AS total_likes_given,
                   countIf(action_type = 'collect') AS total_collects_given,
                   countIf(action_type = 'comment') AS total_comments,
                   countIf(action_type = 'focus') AS total_focus,
                   countIf(action_type = 'view') AS total_views_given,
                   max(action_time) AS last_active_time
            FROM warehouse.dwd_user_action FINAL
            GROUP BY user_id
        ) AS g ON u.id = g.user_id
        LEFT JOIN
        (
            SELECT a.user_id AS author_id,
                   count() AS total_articles,
                   sum(a.views) AS total_views_received,
                   ifNull(l.like_count, 0) AS total_likes_received,
                   ifNull(c.collect_count, 0) AS total_collects_received
            FROM warehouse.dwd_article_event AS a FINAL
            LEFT JOIN
            (
                SELECT article_id, countIf(action_type = 'like') AS like_count
                FROM warehouse.dwd_user_action FINAL
                WHERE article_id > 0
                GROUP BY article_id
            ) AS l ON a.id = l.article_id
            LEFT JOIN
            (
                SELECT article_id, countIf(action_type = 'collect') AS collect_count
                FROM warehouse.dwd_user_action FINAL
                WHERE article_id > 0
                GROUP BY article_id
            ) AS c ON a.id = c.article_id
            GROUP BY a.user_id, l.like_count, c.collect_count
        ) AS p ON u.id = p.author_id
        LEFT JOIN
        (
            SELECT focus_id AS author_id, count() AS total_followers
            FROM warehouse.dwd_user_action FINAL
            WHERE action_type = 'focus' AND article_id > 0
            GROUP BY focus_id
        ) AS f ON u.id = f.author_id
    """

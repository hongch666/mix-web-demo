from datetime import datetime
from typing import Final, Sequence


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

    ODS_API_LOG_TABLE: Final[str] = "ods_api_log"
    ODS_API_LOG_COLUMNS: Final[tuple[str, ...]] = (
        "event_id",
        "user_id",
        "username",
        "api_description",
        "api_path",
        "api_method",
        "response_time",
        "created_at",
    )
    ODS_API_LOG_INSERT: Final[str] = (
        "INSERT INTO warehouse.ods_api_log "
        "(event_id, user_id, username, api_description, api_path, api_method, "
        "response_time, created_at) VALUES"
    )

    API_AVERAGE_SPEED_QUERY: Final[str] = """
        SELECT api_path, api_method, api_description, avg_response_time, call_count
        FROM warehouse.ads_api_average_speed FINAL
        ORDER BY avg_response_time DESC
    """
    API_CALLED_COUNT_QUERY: Final[str] = """
        SELECT api_path, api_method, api_description, call_count, avg_response_time
        FROM warehouse.ads_api_called_count FINAL
        ORDER BY call_count DESC
    """
    SEARCH_KEYWORDS_QUERY: Final[str] = """
        SELECT keyword
        FROM warehouse.ads_search_keywords FINAL
        ORDER BY keyword
    """

    # ========== 数仓库表自动初始化（定时任务前置检查，幂等） ==========
    WAREHOUSE_DATABASE_DDL: Final[str] = "CREATE DATABASE IF NOT EXISTS warehouse"
    WAREHOUSE_TABLE_EXISTS_QUERY: Final[str] = "EXISTS TABLE {table}"

    WAREHOUSE_DDL: Final[tuple[tuple[str, str], ...]] = (
        (
            "sync_watermark",
            """
            CREATE TABLE IF NOT EXISTS warehouse.sync_watermark (
                table_name String,
                last_watermark String,
                updated_at DateTime
            ) ENGINE = ReplacingMergeTree (updated_at)
            ORDER BY table_name
            """,
        ),
        (
            "ods_articles",
            """
            CREATE TABLE IF NOT EXISTS warehouse.ods_articles (
                id Int64, title String, user_id Int64, sub_category_id Int64,
                tags String, status Int8, views Int32,
                create_at DateTime, update_at DateTime
            ) ENGINE = ReplacingMergeTree (update_at) ORDER BY id
            """,
        ),
        (
            "ods_user",
            """
            CREATE TABLE IF NOT EXISTS warehouse.ods_user (
                id Int64, name String, role String, img String, signature String,
                create_at DateTime, update_at DateTime
            ) ENGINE = ReplacingMergeTree (update_at) ORDER BY id
            """,
        ),
        (
            "ods_category",
            """
            CREATE TABLE IF NOT EXISTS warehouse.ods_category (
                id Int64, name String,
                create_time DateTime, update_time DateTime
            ) ENGINE = ReplacingMergeTree (update_time) ORDER BY id
            """,
        ),
        (
            "ods_sub_category",
            """
            CREATE TABLE IF NOT EXISTS warehouse.ods_sub_category (
                id Int64, name String, category_id Int64,
                create_time DateTime, update_time DateTime
            ) ENGINE = ReplacingMergeTree (update_time) ORDER BY id
            """,
        ),
        (
            "ods_likes",
            """
            CREATE TABLE IF NOT EXISTS warehouse.ods_likes (
                id Int64, article_id Int64, user_id Int64, created_time DateTime
            ) ENGINE = ReplacingMergeTree (created_time) ORDER BY id
            """,
        ),
        (
            "ods_collects",
            """
            CREATE TABLE IF NOT EXISTS warehouse.ods_collects (
                id Int64, article_id Int64, user_id Int64, created_time DateTime
            ) ENGINE = ReplacingMergeTree (created_time) ORDER BY id
            """,
        ),
        (
            "ods_comments",
            """
            CREATE TABLE IF NOT EXISTS warehouse.ods_comments (
                id Int64, user_id Int64, article_id Int64, star Float64,
                create_time DateTime, update_time DateTime
            ) ENGINE = ReplacingMergeTree (update_time) ORDER BY id
            """,
        ),
        (
            "ods_focus",
            """
            CREATE TABLE IF NOT EXISTS warehouse.ods_focus (
                id Int64, user_id Int64, focus_id Int64, created_time DateTime
            ) ENGINE = ReplacingMergeTree (created_time) ORDER BY id
            """,
        ),
        (
            "ods_article_log",
            """
            CREATE TABLE IF NOT EXISTS warehouse.ods_article_log (
                event_id String, user_id Int64, article_id Int64,
                action String, content String, created_at DateTime
            ) ENGINE = ReplacingMergeTree (created_at) ORDER BY event_id
            """,
        ),
        (
            "ods_api_log",
            """
            CREATE TABLE IF NOT EXISTS warehouse.ods_api_log (
                event_id String, user_id Int64, username String,
                api_description String, api_path String, api_method String,
                response_time Float64, created_at DateTime
            ) ENGINE = ReplacingMergeTree (created_at) ORDER BY event_id
            """,
        ),
        (
            "dim_user",
            """
            CREATE TABLE IF NOT EXISTS warehouse.dim_user (
                id Int64, name String, role String, img String, signature String,
                create_at DateTime, update_at DateTime
            ) ENGINE = ReplacingMergeTree (update_at) ORDER BY id
            """,
        ),
        (
            "dim_category",
            """
            CREATE TABLE IF NOT EXISTS warehouse.dim_category (
                sub_category_id Int64, sub_category_name String,
                parent_category_id Int64, parent_category_name String,
                update_time DateTime
            ) ENGINE = ReplacingMergeTree (update_time) ORDER BY sub_category_id
            """,
        ),
        (
            "dwd_article_event",
            """
            CREATE TABLE IF NOT EXISTS warehouse.dwd_article_event (
                id Int64, title String, user_id Int64, views Int32, status Int8,
                sub_category_id Int64, parent_category_id Int64,
                parent_category_name String, create_date Date,
                create_at DateTime, update_at DateTime
            ) ENGINE = ReplacingMergeTree (update_at) ORDER BY id
            """,
        ),
        (
            "dwd_user_action",
            """
            CREATE TABLE IF NOT EXISTS warehouse.dwd_user_action (
                event_id String, source_type String, source_id Int64,
                action_type String, user_id Int64, article_id Int64,
                action_date Date, action_time DateTime
            ) ENGINE = ReplacingMergeTree (action_time) ORDER BY event_id
            """,
        ),
        (
            "dws_article_day",
            """
            CREATE TABLE IF NOT EXISTS warehouse.dws_article_day (
                stat_date Date, article_id Int64, user_id Int64,
                parent_category_id Int64, views Int64, like_count Int64,
                collect_count Int64, comment_count Int64, view_count Int64
            ) ENGINE = MergeTree ORDER BY (stat_date, article_id)
            """,
        ),
        (
            "dws_user_day",
            """
            CREATE TABLE IF NOT EXISTS warehouse.dws_user_day (
                stat_date Date, user_id Int64, like_count Int64,
                collect_count Int64, comment_count Int64, focus_count Int64,
                liked_articles UInt64, last_active_time DateTime
            ) ENGINE = MergeTree ORDER BY (stat_date, user_id)
            """,
        ),
        (
            "ads_user_day",
            """
            CREATE TABLE IF NOT EXISTS warehouse.ads_user_day (
                stat_date Date, user_id Int64, like_count Int64,
                collect_count Int64, comment_count Int64, focus_count Int64,
                view_count Int64, last_active_time DateTime, stat_time DateTime
            ) ENGINE = ReplacingMergeTree (stat_time) ORDER BY (stat_date, user_id)
            """,
        ),
        (
            "ads_user_view_articles",
            """
            CREATE TABLE IF NOT EXISTS warehouse.ads_user_view_articles (
                user_id Int64, article_id Int64, article_title String,
                view_count Int64, stat_time DateTime
            ) ENGINE = ReplacingMergeTree (stat_time) ORDER BY (user_id, article_id)
            """,
        ),
        (
            "ads_user_stats",
            """
            CREATE TABLE IF NOT EXISTS warehouse.ads_user_stats (
                user_id Int64, total_likes_given Int64, total_collects_given Int64,
                total_comments Int64, total_focus Int64, total_views_given Int64,
                total_articles Int64, total_views_received Int64,
                total_likes_received Int64, total_collects_received Int64,
                total_followers Int64, last_active_time DateTime, stat_time DateTime
            ) ENGINE = ReplacingMergeTree (stat_time) ORDER BY user_id
            """,
        ),
        (
            "ads_top10_articles",
            """
            CREATE TABLE IF NOT EXISTS warehouse.ads_top10_articles (
                id Int64, title String, tags String, status Int8, views Int32,
                create_at DateTime, update_at DateTime, user_id Int64,
                sub_category_id Int64, stat_time DateTime
            ) ENGINE = ReplacingMergeTree (stat_time) ORDER BY id
            """,
        ),
        (
            "ads_category_stats",
            """
            CREATE TABLE IF NOT EXISTS warehouse.ads_category_stats (
                parent_category_id Int64, category_name String,
                article_count Int64, stat_time DateTime
            ) ENGINE = ReplacingMergeTree (stat_time) ORDER BY parent_category_id
            """,
        ),
        (
            "ads_monthly_publish",
            """
            CREATE TABLE IF NOT EXISTS warehouse.ads_monthly_publish (
                year_month String, article_count Int64, stat_time DateTime
            ) ENGINE = ReplacingMergeTree (stat_time) ORDER BY year_month
            """,
        ),
        (
            "ads_platform_stats",
            """
            CREATE TABLE IF NOT EXISTS warehouse.ads_platform_stats (
                id UInt8, stat_time DateTime, total_views Int64,
                total_articles Int64, active_authors UInt64, average_views Float64,
                total_likes Int64, average_likes Float64, total_collects Int64,
                average_collects Float64
            ) ENGINE = ReplacingMergeTree (stat_time) ORDER BY id
            """,
        ),
        (
            "ads_api_average_speed",
            """
            CREATE TABLE IF NOT EXISTS warehouse.ads_api_average_speed (
                api_path String, api_method String, api_description String,
                avg_response_time Float64, call_count Int64, stat_time DateTime
            ) ENGINE = ReplacingMergeTree (stat_time)
            ORDER BY (api_path, api_method, api_description)
            """,
        ),
        (
            "ads_api_called_count",
            """
            CREATE TABLE IF NOT EXISTS warehouse.ads_api_called_count (
                api_path String, api_method String, api_description String,
                call_count Int64, avg_response_time Float64, stat_time DateTime
            ) ENGINE = ReplacingMergeTree (stat_time)
            ORDER BY (api_path, api_method, api_description)
            """,
        ),
        (
            "ads_search_keywords",
            """
            CREATE TABLE IF NOT EXISTS warehouse.ads_search_keywords (
                keyword String, stat_time DateTime
            ) ENGINE = ReplacingMergeTree (stat_time) ORDER BY keyword
            """,
        ),
    )

    # 水位线初始化：仅为首次出现的表写入纪元水位（与 init.sql 逻辑一致）
    WAREHOUSE_WATERMARK_INIT: Final[str] = (
        "INSERT INTO warehouse.sync_watermark (table_name, last_watermark, updated_at) "
        "SELECT table_name, '1970-01-01 00:00:00', now() "
        "FROM (SELECT arrayJoin(['ods_articles', 'ods_user', 'ods_category', "
        "'ods_sub_category', 'ods_likes', 'ods_collects', 'ods_comments', "
        "'ods_focus', 'ods_article_log', 'ods_api_log']) AS table_name) "
        "WHERE table_name NOT IN "
        "(SELECT table_name FROM warehouse.sync_watermark FINAL)"
    )

    @staticmethod
    def ODS_REMOTE_INSERT(table_name: str, columns: Sequence[str]) -> str:
        """远程数据源同步 INSERT 模板：表名与列名均来自 REMOTE_SOURCES 内部常量"""
        return f"INSERT INTO warehouse.{table_name} ({', '.join(columns)}) VALUES"

    BATCH_SIZE: Final[int] = 1000
    ARTICLE_LOG_BATCH_SIZE: Final[int] = 5000
    EPOCH_WATERMARK: Final[str] = "1970-01-01 00:00:00"
    EPOCH_DATETIME: Final[datetime] = datetime(1970, 1, 1)
    REMOTE_SOURCES: Final[tuple[tuple[str, str, tuple[str, ...]], ...]] = (
        (
            "ods_articles",
            "articles",
            (
                "id",
                "title",
                "user_id",
                "sub_category_id",
                "tags",
                "status",
                "views",
                "create_at",
                "update_at",
            ),
        ),
        (
            "ods_user",
            "user",
            ("id", "name", "role", "img", "signature", "create_at", "update_at"),
        ),
        ("ods_category", "category", ("id", "name", "create_time", "update_time")),
        (
            "ods_sub_category",
            "sub_category",
            ("id", "name", "category_id", "create_time", "update_time"),
        ),
        ("ods_likes", "likes", ("id", "article_id", "user_id", "created_time")),
        ("ods_collects", "collects", ("id", "article_id", "user_id", "created_time")),
        (
            "ods_comments",
            "comments",
            ("id", "user_id", "article_id", "star", "create_time", "update_time"),
        ),
        ("ods_focus", "focus", ("id", "user_id", "focus_id", "created_time")),
    )
    DATETIME_COLUMNS: Final[frozenset[str]] = frozenset(
        {"create_at", "update_at", "create_time", "update_time", "created_time"}
    )
    STRING_COLUMNS: Final[frozenset[str]] = frozenset(
        {"tags", "role", "img", "signature", "title", "name"}
    )
    INTEGER_COLUMNS: Final[frozenset[str]] = frozenset(
        {
            "status",
            "views",
            "id",
            "user_id",
            "article_id",
            "sub_category_id",
            "category_id",
            "focus_id",
        }
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
        "TRUNCATE TABLE warehouse.dwd_api_call",
        "TRUNCATE TABLE warehouse.dws_api_day",
        "TRUNCATE TABLE warehouse.ads_api_average_speed",
        "TRUNCATE TABLE warehouse.ads_api_called_count",
        "TRUNCATE TABLE warehouse.ads_search_keywords",
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
            SELECT article_id AS author_id, count() AS total_followers
            FROM warehouse.dwd_user_action FINAL
            WHERE action_type = 'focus' AND article_id > 0
            GROUP BY article_id
        ) AS f ON u.id = f.author_id
    """

    # API 日志 DWD 层：ODS 明细补齐日期维度
    REFRESH_DWD_API_CALL: Final[str] = """
        INSERT INTO warehouse.dwd_api_call
        SELECT event_id, api_path, api_method, api_description, user_id, username,
               response_time, toDate(created_at), created_at
        FROM warehouse.ods_api_log FINAL
    """

    # API 日志 DWS 层：按日 + 接口维度轻度聚合
    REFRESH_DWS_API_DAY: Final[str] = """
        INSERT INTO warehouse.dws_api_day
        SELECT action_date, api_path, api_method, api_description,
               count(), sum(response_time), max(response_time)
        FROM warehouse.dwd_api_call FINAL
        GROUP BY action_date, api_path, api_method, api_description
    """

    # API 日志 ADS 层刷新：平均响应速度与调用次数（与远程聚合接口输出同构）
    REFRESH_ADS_API: Final[tuple[str, ...]] = (
        """
        INSERT INTO warehouse.ads_api_average_speed
        SELECT api_path, api_method, api_description,
               round(sum(total_response_time) / greatest(sum(call_count), 1), 2),
               sum(call_count), now()
        FROM warehouse.dws_api_day
        GROUP BY api_path, api_method, api_description
        """,
        """
        INSERT INTO warehouse.ads_api_called_count
        SELECT api_path, api_method, api_description,
               sum(call_count),
               round(sum(total_response_time) / greatest(sum(call_count), 1), 2), now()
        FROM warehouse.dws_api_day
        GROUP BY api_path, api_method, api_description
        """,
    )

    # 搜索关键词 ADS 层刷新：与 NestJS 词云接口保持相同的去重、排序语义
    REFRESH_ADS_SEARCH_KEYWORDS: Final[str] = """
        INSERT INTO warehouse.ads_search_keywords
        SELECT keyword, now()
        FROM
        (
            SELECT if(
                       JSONExtractString(content, 'Keyword') != '',
                       JSONExtractString(content, 'Keyword'),
                       JSONExtractString(content, '_keyword')
                   ) AS keyword
            FROM warehouse.ods_article_log FINAL
            WHERE action = 'search'
        )
        WHERE keyword != ''
        GROUP BY keyword
    """

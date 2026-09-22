from datetime import datetime
from typing import Final


class WarehouseScripts:
    """ClickHouse 数仓同步和汇总 SQL"""

    ODS_ARTICLE_LOG_TABLE: Final[str] = "ods_article_log"

    ODS_API_LOG_TABLE: Final[str] = "ods_api_log"

    # 水位线旧行清理：ClickHouse 没有行级 UPSERT，写入新水位前先删除同表旧行
    WATERMARK_DELETE_BY_TABLE: Final[str] = (
        "ALTER TABLE warehouse.sync_watermark DELETE WHERE table_name = %(table_name)s"
    )

    # Agent 数仓工具使用的固定 ADS 查询，避免模型直接拼接 ClickHouse SQL
    WAREHOUSE_AGENT_QUERIES: Final[dict[str, str]] = {
        "platform_stats": """
            SELECT total_views, total_articles, active_authors, average_views,
                   total_likes, average_likes, total_collects, average_collects
            FROM warehouse.ads_platform_stats FINAL
            ORDER BY stat_time DESC LIMIT 1
        """,
        "top_articles": """
            SELECT id, title, tags, status, views, create_at, update_at, user_id,
                   sub_category_id
            FROM warehouse.ads_top10_articles FINAL
            ORDER BY views DESC
            LIMIT %(limit)s
        """,
        "category_stats": """
            SELECT parent_category_id, category_name, article_count
            FROM warehouse.ads_category_stats FINAL
            ORDER BY article_count DESC
            LIMIT %(limit)s
        """,
        "monthly_publish": """
            SELECT year_month, article_count
            FROM warehouse.ads_monthly_publish FINAL
            ORDER BY year_month DESC
            LIMIT %(limit)s
        """,
        "api_average_speed": """
            SELECT api_path, api_method, api_description, avg_response_time, call_count
            FROM warehouse.ads_api_average_speed FINAL
            ORDER BY avg_response_time DESC
            LIMIT %(limit)s
        """,
        "api_called_count": """
            SELECT api_path, api_method, api_description, call_count, avg_response_time
            FROM warehouse.ads_api_called_count FINAL
            ORDER BY call_count DESC
            LIMIT %(limit)s
        """,
        "search_keywords": """
            SELECT keyword
            FROM warehouse.ads_search_keywords FINAL
            ORDER BY keyword
            LIMIT %(limit)s
        """,
        "user_profile": """
            SELECT s.user_id, ifNull(u.name, ''), s.total_articles,
                   s.total_views_received, s.total_likes_received,
                   s.total_collects_received, s.total_followers,
                   s.total_likes_given, s.total_collects_given,
                   s.total_comments, s.total_focus, s.last_active_time
            FROM warehouse.ads_user_stats AS s FINAL
            LEFT JOIN warehouse.dim_user AS u FINAL ON s.user_id = u.id
            WHERE s.user_id = %(user_id)s
            LIMIT %(limit)s
        """,
        "user_daily_actions": """
            SELECT stat_date, like_count, collect_count, comment_count,
                   focus_count, view_count, last_active_time
            FROM warehouse.ads_user_day FINAL
            WHERE user_id = %(user_id)s
              AND stat_date >= %(start_date)s AND stat_date < %(end_date)s
            ORDER BY stat_date DESC
            LIMIT %(limit)s
        """,
        "user_view_articles": """
            SELECT article_id, article_title, view_count
            FROM warehouse.ads_user_view_articles FINAL
            WHERE user_id = %(user_id)s
            ORDER BY view_count DESC
            LIMIT %(limit)s
        """,
    }
    WAREHOUSE_AGENT_DATASETS: Final[tuple[str, ...]] = tuple(
        WAREHOUSE_AGENT_QUERIES.keys()
    )
    WAREHOUSE_AGENT_USER_DATASETS: Final[frozenset[str]] = frozenset(
        {"user_profile", "user_daily_actions", "user_view_articles"}
    )
    WAREHOUSE_AGENT_DATASET_DESCRIPTIONS: Final[dict[str, str]] = {
        "platform_stats": "平台总浏览量、文章数、作者数、点赞和收藏",
        "top_articles": "阅读量最高的文章榜单",
        "category_stats": "分类文章数量",
        "monthly_publish": "月度文章发布趋势",
        "api_average_speed": "接口平均响应时间",
        "api_called_count": "接口调用次数",
        "search_keywords": "搜索关键词集合",
        "user_profile": "指定用户的累计画像指标",
        "user_daily_actions": "指定用户的日行为汇总",
        "user_view_articles": "指定用户浏览文章及次数",
    }
    WAREHOUSE_AGENT_RESULT_COLUMNS: Final[dict[str, list[str]]] = {
        "platform_stats": [
            "total_views",
            "total_articles",
            "active_authors",
            "average_views",
            "total_likes",
            "average_likes",
            "total_collects",
            "average_collects",
        ],
        "top_articles": [
            "id",
            "title",
            "tags",
            "status",
            "views",
            "create_at",
            "update_at",
            "user_id",
            "sub_category_id",
        ],
        "category_stats": ["parent_category_id", "category_name", "article_count"],
        "monthly_publish": ["year_month", "article_count"],
        "api_average_speed": [
            "api_path",
            "api_method",
            "api_description",
            "avg_response_time",
            "call_count",
        ],
        "api_called_count": [
            "api_path",
            "api_method",
            "api_description",
            "call_count",
            "avg_response_time",
        ],
        "search_keywords": ["keyword"],
        "user_profile": [
            "user_id",
            "user_name",
            "total_articles",
            "total_views_received",
            "total_likes_received",
            "total_collects_received",
            "total_followers",
            "total_likes_given",
            "total_collects_given",
            "total_comments",
            "total_focus",
            "last_active_time",
        ],
        "user_daily_actions": [
            "stat_date",
            "like_count",
            "collect_count",
            "comment_count",
            "focus_count",
            "view_count",
            "last_active_time",
        ],
        "user_view_articles": ["article_id", "article_title", "view_count"],
    }

    # ========== 数仓刷新 SQL（复杂多表聚合由 ClickHouse 执行） ==========
    BATCH_SIZE: Final[int] = 1000
    ARTICLE_LOG_BATCH_SIZE: Final[int] = 5000
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

    # 数仓增量刷新说明
    # 派生表分两类维护方式：
    #   1) 分区表：按日期累积增长，仅重建本次有新数据涉及的月份分区，避免每分钟全量重建
    #   2) 快照表：维度表与全局聚合快照，数据量小且无日期分区，每次有新数据时全量重建
    # 两类表的执行顺序与 SQL 见文件末尾的 REFRESH_SEQUENCE

    # ODS 源表 -> 用于推导脏分区的日期字段
    # 同步时按该字段取出行内日期，作为需要重建的月份分区
    SOURCE_DIRTY_DATE_FIELD: Final[dict[str, str]] = {
        "ods_article_log": "created_at",
        "ods_api_log": "created_at",
        "ods_likes": "created_time",
        "ods_collects": "created_time",
        "ods_comments": "create_time",
        "ods_focus": "created_time",
    }

    # 分区值模板：分区键由 toYYYYMM 生成，形如 202609
    PARTITION_VALUE_TEMPLATE: Final[str] = "toString(toYYYYMM(%s)) = %(partition)s"

    # 分区清理模板：表名与分区值为内部生成的常量（分区值必为纯数字），
    # ClickHouse 的 DROP PARTITION 不接受绑定参数，与项目内其他 DDL 模板同样采用受控拼接
    PARTITION_DROP_TEMPLATE: Final[str] = "ALTER TABLE warehouse.%s DROP PARTITION %s"

    TRUNCATE_TEMPLATE: Final[str] = "TRUNCATE TABLE warehouse.%s"

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
        -- 关注行的 article_id 存被关注用户 ID，与 ods_focus 的 focus_id 语义一致
        SELECT event_id, 'article_log', 0, action, user_id, article_id,
               toDate(created_at), created_at FROM warehouse.ods_article_log FINAL
        WHERE toString(toYYYYMM(created_at)) = %(partition)s
        UNION ALL
        -- 补充数据源：仅取事件流起点之前的关系表存量，避免与事件流重复计数
        SELECT concat('like:', toString(id)), 'likes', id, 'like', user_id,
               article_id, toDate(created_time), created_time FROM warehouse.ods_likes FINAL
        WHERE created_time < (SELECT ifNull(min(created_at), toDateTime('1970-01-01 00:00:00')) FROM warehouse.ods_article_log)
          AND toString(toYYYYMM(created_time)) = %(partition)s
        UNION ALL
        SELECT concat('collect:', toString(id)), 'collects', id, 'collect', user_id,
               article_id, toDate(created_time), created_time FROM warehouse.ods_collects FINAL
        WHERE created_time < (SELECT ifNull(min(created_at), toDateTime('1970-01-01 00:00:00')) FROM warehouse.ods_article_log)
          AND toString(toYYYYMM(created_time)) = %(partition)s
        UNION ALL
        SELECT concat('comment:', toString(id)), 'comments', id, 'comment', user_id,
               article_id, toDate(create_time), create_time FROM warehouse.ods_comments FINAL
        WHERE create_time < (SELECT ifNull(min(created_at), toDateTime('1970-01-01 00:00:00')) FROM warehouse.ods_article_log)
          AND toString(toYYYYMM(create_time)) = %(partition)s
        UNION ALL
        SELECT concat('focus:', toString(id)), 'focus', id, 'focus', user_id,
               focus_id, toDate(created_time), created_time FROM warehouse.ods_focus FINAL
        WHERE created_time < (SELECT ifNull(min(created_at), toDateTime('1970-01-01 00:00:00')) FROM warehouse.ods_article_log)
          AND toString(toYYYYMM(created_time)) = %(partition)s
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
              AND toString(toYYYYMM(action_date)) = %(partition)s
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
        WHERE toString(toYYYYMM(action_date)) = %(partition)s
        GROUP BY action_date, user_id
    """
    REFRESH_ADS: Final[tuple[str, ...]] = (
        """
        INSERT INTO warehouse.ads_top10_articles
        SELECT a.id, a.title, '', a.status, a.views, a.create_at, a.update_at,
               a.user_id, ifNull(u.name, ''), a.sub_category_id, now()
        FROM warehouse.dwd_article_event AS a FINAL
        LEFT JOIN warehouse.dim_user AS u FINAL ON a.user_id = u.id
        ORDER BY a.views DESC LIMIT 10
        """,
        """
        INSERT INTO warehouse.ads_category_stats
        SELECT parent_category_id, any(parent_category_name), count(), now()
        FROM warehouse.dwd_article_event FINAL GROUP BY parent_category_id
        """,
        # 不能用 formatDateTime(create_at, '%Y-%m')：SQL 走驱动 pyformat 参数化，
        # % 会被当成占位符导致 unsupported format character 报错，改等价字符串截取
        """
        INSERT INTO warehouse.ads_monthly_publish
        SELECT substring(toString(create_at), 1, 7), count(), now()
        FROM warehouse.dwd_article_event FINAL
        WHERE create_at >= subtractMonths(now(), 24)
        GROUP BY substring(toString(create_at), 1, 7)
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
        WHERE toString(toYYYYMM(action_date)) = %(partition)s
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
        WHERE toString(toYYYYMM(created_at)) = %(partition)s
    """

    # API 日志 DWS 层：按日 + 接口维度轻度聚合
    REFRESH_DWS_API_DAY: Final[str] = """
        INSERT INTO warehouse.dws_api_day
        SELECT action_date, api_path, api_method, api_description,
               count(), sum(response_time), max(response_time)
        FROM warehouse.dwd_api_call FINAL
        WHERE toString(toYYYYMM(action_date)) = %(partition)s
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

    # ========== 派生层刷新执行顺序 ==========
    # 分区增量表：表名 -> (分区清理后需执行的 INSERT SQL, 分区日期列)
    # 刷新流程对每个脏分区执行 DROP PARTITION + INSERT，只重建受影响月份
    PARTITIONED_REFRESH_STEPS: Final[dict[str, tuple[str, str]]] = {
        "dwd_user_action": (REFRESH_DWD_ACTION, "action_date"),
        "dwd_api_call": (REFRESH_DWD_API_CALL, "action_date"),
        "dws_article_day": (REFRESH_DWS_ARTICLE, "stat_date"),
        "dws_user_day": (REFRESH_DWS_USER, "stat_date"),
        "dws_api_day": (REFRESH_DWS_API_DAY, "action_date"),
        "ads_user_day": (REFRESH_ADS_USER_DAY, "stat_date"),
    }

    # 分区表的依赖顺序：上游分区表必须先于下游重建
    PARTITIONED_REFRESH_ORDER: Final[tuple[str, ...]] = (
        "dwd_user_action",
        "dwd_api_call",
        "dws_article_day",
        "dws_user_day",
        "dws_api_day",
        "ads_user_day",
    )

    # 全量重建表：表名 -> INSERT SQL，按依赖顺序排列
    # 依赖关系：dim_* -> dwd_article_event -> ads_*（用户累计指标依赖前面全部表）
    FULL_REFRESH_STEPS: Final[tuple[tuple[str, str], ...]] = (
        ("dim_user", REFRESH_DIM_USER),
        ("dim_category", REFRESH_DIM_CATEGORY),
        ("dwd_article_event", REFRESH_DWD_ARTICLE),
        ("ads_top10_articles", REFRESH_ADS[0]),
        ("ads_category_stats", REFRESH_ADS[1]),
        ("ads_monthly_publish", REFRESH_ADS[2]),
        ("ads_platform_stats", REFRESH_ADS[3]),
        ("ads_user_view_articles", REFRESH_ADS_USER_VIEW_ARTICLES),
        ("ads_user_stats", REFRESH_ADS_USER_STATS),
        ("ads_api_average_speed", REFRESH_ADS_API[0]),
        ("ads_api_called_count", REFRESH_ADS_API[1]),
        ("ads_search_keywords", REFRESH_ADS_SEARCH_KEYWORDS),
    )

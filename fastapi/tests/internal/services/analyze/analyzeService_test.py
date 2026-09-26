import importlib
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.constants import HttpCode, Messages
from app.core.errors import BusinessException
from app.internal.services.analyze.analyzeService import AnalyzeService

analyze_module = importlib.import_module("app.internal.services.analyze.analyzeService")


def _fake_cache(return_value=None) -> MagicMock:
    cache = MagicMock()
    cache.get = AsyncMock(return_value=return_value)
    cache.set = AsyncMock()
    return cache


def _make_service(**overrides) -> AnalyzeService:
    defaults: dict[str, object] = {
        "articleMapper": AsyncMock(),
        "article_cache": _fake_cache(),
        "category_cache": _fake_cache(),
        "publish_time_cache": _fake_cache(),
        "statistics_cache": _fake_cache(),
        "wordcloud_cache": _fake_cache(),
        "spring_client": AsyncMock(),
        "nestjs_client": AsyncMock(),
    }
    defaults.update(overrides)
    return AnalyzeService(**defaults)


# ===== singleflight =====


# 缓存命中时直接返回结果且不触发加载函数
@pytest.mark.anyio
async def test_singleflight_returns_cached_without_loading() -> None:
    service = _make_service()
    cache_getter = AsyncMock(return_value=[{"id": 1}])
    loader = AsyncMock(return_value=[{"id": 2}])

    result = await service._run_with_singleflight("k", cache_getter, loader)

    assert result == [{"id": 1}]
    loader.assert_not_awaited()


# 进入锁后二次读取缓存命中则跳过加载函数
@pytest.mark.anyio
async def test_singleflight_rechecks_cache_inside_lock() -> None:
    service = _make_service()
    values = iter([None, [{"id": 9}]])

    async def cache_getter():  # noqa: ANN202
        return next(values)

    loader = AsyncMock()

    result = await service._run_with_singleflight("k", cache_getter, loader)

    assert result == [{"id": 9}]
    loader.assert_not_awaited()


# 缓存全未命中时执行加载函数并返回其结果
@pytest.mark.anyio
async def test_singleflight_loads_on_full_miss() -> None:
    service = _make_service()
    cache_getter = AsyncMock(return_value=None)
    loader = AsyncMock(return_value=[{"id": 3}])

    result = await service._run_with_singleflight("k", cache_getter, loader)

    assert result == [{"id": 3}]
    loader.assert_awaited_once()


# Top10 包装器使用 analyze:top10 作为 singleflight 键
@pytest.mark.anyio
async def test_top10_singleflight_wrapper_uses_expected_key() -> None:
    service = _make_service()
    service._run_with_singleflight = AsyncMock(return_value=["x"])
    service.get_top10_articles_service = AsyncMock(return_value=["y"])  # type: ignore[method-assign]
    db = MagicMock()

    result = await service.get_top10_articles_service_sf(db)

    assert result == ["x"]
    call = service._run_with_singleflight.await_args
    assert call.args[0] == "analyze:top10"
    loader = call.args[2]
    assert await loader() == ["y"]
    service.get_top10_articles_service.assert_awaited_once_with(db)


# 缓存读取异常被吞掉并返回 None
@pytest.mark.anyio
async def test_cache_getter_swallows_backend_error() -> None:
    service = _make_service(article_cache=_fake_cache())
    service._article_cache.get = AsyncMock(side_effect=RuntimeError("redis down"))

    assert await service._get_top10_cached() is None


# ===== Top10 文章 =====


# Top10 命中缓存时不查询 ClickHouse 与 Spring
@pytest.mark.anyio
async def test_top10_returns_cached_without_querying_upstream() -> None:
    articles = [{"user_id": 1, "username": "a"}]
    service = _make_service(article_cache=_fake_cache(return_value=articles))

    result = await service.get_top10_articles_service(MagicMock())

    assert result == articles
    service.articleMapper.get_top10_articles_clickhouse_mapper_async.assert_not_awaited()
    service._spring_client.get_top10_articles.assert_not_awaited()


# Top10 优先取 ClickHouse 结果并写回缓存
@pytest.mark.anyio
async def test_top10_prefers_clickhouse_and_updates_cache() -> None:
    rows = [{"user_id": 1, "username": "a", "views": 5}]
    mapper = AsyncMock()
    mapper.get_top10_articles_clickhouse_mapper_async = AsyncMock(return_value=rows)
    service = _make_service(articleMapper=mapper)

    result = await service.get_top10_articles_service(MagicMock())

    assert result == rows
    service._article_cache.set.assert_awaited_once_with(rows)
    service._spring_client.get_top10_articles.assert_not_awaited()


# ClickHouse 失败时降级 Spring 并补齐缺失的用户名
@pytest.mark.anyio
async def test_top10_degrades_to_spring_and_fills_missing_username() -> None:
    mapper = AsyncMock()
    mapper.get_top10_articles_clickhouse_mapper_async = AsyncMock(
        side_effect=RuntimeError("ch down")
    )
    spring = AsyncMock()
    spring.get_top10_articles.return_value = [{"user_id": 2, "views": 3}]
    spring.get_users_by_ids.return_value = [{"id": 2, "name": "bob"}]
    service = _make_service(articleMapper=mapper, spring_client=spring)

    result = await service.get_top10_articles_service(MagicMock())

    assert result[0]["username"] == "bob"
    spring.get_users_by_ids.assert_awaited_once_with([2])


# Top10 结果中的时间字段转换为 ISO 字符串
@pytest.mark.anyio
async def test_top10_converts_datetime_fields_to_isoformat() -> None:
    created = datetime(2026, 1, 2, 3, 4, 5)
    rows = [{"user_id": 1, "username": "a", "create_at": created, "update_at": created}]
    mapper = AsyncMock()
    mapper.get_top10_articles_clickhouse_mapper_async = AsyncMock(return_value=rows)
    service = _make_service(articleMapper=mapper)

    result = await service.get_top10_articles_service(MagicMock())

    assert result[0]["create_at"] == created.isoformat()
    assert result[0]["update_at"] == created.isoformat()


# 缓存写入失败时仍返回 ClickHouse 查询结果
@pytest.mark.anyio
async def test_top10_returns_result_when_cache_update_fails() -> None:
    rows = [{"user_id": 1, "username": "a"}]
    mapper = AsyncMock()
    mapper.get_top10_articles_clickhouse_mapper_async = AsyncMock(return_value=rows)
    cache = _fake_cache()
    cache.set = AsyncMock(side_effect=RuntimeError("cache write failed"))
    service = _make_service(articleMapper=mapper, article_cache=cache)

    result = await service.get_top10_articles_service(MagicMock())

    assert result == rows


# ===== 搜索关键词 =====


# 关键词优先取 ClickHouse 结果并统计词频，不调用 NestJS
@pytest.mark.anyio
async def test_keywords_dic_prefers_ads_source() -> None:
    mapper = AsyncMock()
    mapper.get_search_keywords_clickhouse_mapper_async = AsyncMock(
        return_value=["python", "ai"]
    )
    service = _make_service(articleMapper=mapper)

    assert await service.get_keywords_dic() == {"python": 1, "ai": 1}
    service._nestjs_client.get_search_keywords.assert_not_awaited()


# ClickHouse 关键词为空时降级调用 NestJS 获取
@pytest.mark.anyio
async def test_keywords_dic_falls_back_to_nestjs_when_ads_empty() -> None:
    mapper = AsyncMock()
    mapper.get_search_keywords_clickhouse_mapper_async = AsyncMock(return_value=[])
    nestjs = AsyncMock()
    nestjs.get_search_keywords.return_value = ["x"]
    service = _make_service(articleMapper=mapper, nestjs_client=nestjs)

    assert await service.get_keywords_dic() == {"x": 1}


# ClickHouse 关键词查询异常时降级调用 NestJS
@pytest.mark.anyio
async def test_keywords_dic_falls_back_to_nestjs_when_ads_raises() -> None:
    mapper = AsyncMock()
    mapper.get_search_keywords_clickhouse_mapper_async = AsyncMock(
        side_effect=RuntimeError("ch down")
    )
    nestjs = AsyncMock()
    nestjs.get_search_keywords.return_value = ["y"]
    service = _make_service(articleMapper=mapper, nestjs_client=nestjs)

    assert await service.get_keywords_dic() == {"y": 1}


# ===== OSS 上传 =====


# 上传文件返回 NestJS 响应中的 OSS 地址并透传本地与目标路径
@pytest.mark.anyio
async def test_upload_file_returns_oss_url() -> None:
    nestjs = AsyncMock()
    nestjs.upload_file.return_value = {"data": "https://oss/pic/x.png"}
    service = _make_service(nestjs_client=nestjs)

    result = await service.upload_file("local.png", "pic/x.png")

    assert result == "https://oss/pic/x.png"
    nestjs.upload_file.assert_awaited_once_with("local.png", "pic/x.png")


# 远端上传失败时将异常原样向上抛出
@pytest.mark.anyio
async def test_upload_file_reraises_remote_failure() -> None:
    nestjs = AsyncMock()
    nestjs.upload_file.side_effect = RuntimeError("oss down")
    service = _make_service(nestjs_client=nestjs)

    with pytest.raises(RuntimeError, match="oss down"):
        await service.upload_file("a", "b")


# 词云上传按配置拼接 pic 目录的 OSS 路径与文件名
@pytest.mark.anyio
async def test_upload_wordcloud_builds_oss_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        analyze_module,
        "load_config",
        lambda section=None, key=None: (
            {"pic_path": "static/pic"} if section == "files" else {}
        ),
    )
    service = _make_service()
    service.upload_file = AsyncMock(return_value="u")  # type: ignore[method-assign]

    result = await service.upload_wordcloud_to_oss()

    assert result == "u"
    kwargs = service.upload_file.await_args.kwargs
    assert kwargs["oss_path"].startswith("pic/")
    assert kwargs["oss_path"].endswith(".png")
    assert kwargs["file_path"].endswith(Messages.WORDCLOUD_FILENAME)


# ===== 词云 =====


# 关键词为空时生成词云抛出参数校验失败业务异常
def test_generate_wordcloud_raises_on_empty_keywords() -> None:
    service = _make_service()

    with pytest.raises(BusinessException) as error:
        service.generate_wordcloud({})

    assert error.value.status_code == HttpCode.BAD_REQUEST
    assert error.value.error == Messages.ERROR_PARAM_PARSE_FAILED


# 按 wordcloud 配置构造词云并保存到配置目录
def test_generate_wordcloud_writes_file_from_config(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    created: list = []

    class _FakeWordCloud:
        def __init__(self, **kwargs) -> None:
            self.kwargs = kwargs
            self.frequencies = None
            self.saved_path = None

        def generate_from_frequencies(self, frequencies) -> None:  # noqa: ANN001
            self.frequencies = frequencies

        def to_file(self, path: str) -> None:
            self.saved_path = path

    def factory(**kwargs) -> _FakeWordCloud:
        instance = _FakeWordCloud(**kwargs)
        created.append(instance)
        return instance

    def fake_load_config(section=None, key=None):  # noqa: ANN001
        if section == "wordcloud":
            return {
                "font_path": "font.ttf",
                "width": 800,
                "height": 600,
                "background_color": "white",
            }
        if section == "files":
            return {"pic_path": "static/pic"}
        return {}

    monkeypatch.setattr(analyze_module, "WordCloud", factory)
    monkeypatch.setattr(analyze_module, "load_config", fake_load_config)

    service = _make_service()
    service.generate_wordcloud({"python": 2, "ai": 1})

    wc = created[0]
    assert wc.kwargs == {
        "font_path": "font.ttf",
        "width": 800,
        "height": 600,
        "background_color": "white",
    }
    assert wc.frequencies == {"python": 2, "ai": 1}
    assert wc.saved_path.endswith("search_keywords_wordcloud.png")


# 词云服务命中缓存时直接返回地址且不生成
@pytest.mark.anyio
async def test_wordcloud_service_returns_cached_url() -> None:
    cache = _fake_cache(return_value="https://oss/cached.png")
    service = _make_service(wordcloud_cache=cache)
    service.get_keywords_dic = AsyncMock()  # type: ignore[method-assign]

    assert await service.get_wordcloud_service() == "https://oss/cached.png"
    service.get_keywords_dic.assert_not_awaited()


# 词云未命中缓存时生成并上传后写入缓存
@pytest.mark.anyio
async def test_wordcloud_service_generates_and_caches_on_miss() -> None:
    cache = _fake_cache(return_value=None)
    service = _make_service(wordcloud_cache=cache)
    service.get_keywords_dic = AsyncMock(return_value={"python": 1})  # type: ignore[method-assign]
    service.generate_wordcloud = MagicMock()  # type: ignore[method-assign]
    service.upload_wordcloud_to_oss = AsyncMock(return_value="https://oss/new.png")  # type: ignore[method-assign]

    result = await service.get_wordcloud_service()

    assert result == "https://oss/new.png"
    service.generate_wordcloud.assert_called_once_with({"python": 1})
    cache.set.assert_awaited_once_with("https://oss/new.png")


# ===== Excel 导出 =====


# 导出文章为 Excel 时写入提示行、表头与含 ISO 时间的数据行
@pytest.mark.anyio
async def test_export_articles_to_excel_appends_rows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    created: list = []

    class _FakeWorkbook:
        def __init__(self, **kwargs) -> None:
            self.rows: list = []
            self.saved_path = None
            created.append(self)

        def create_sheet(self, title: str) -> "_FakeWorkbook":
            self.sheet_title = title
            return self

        def append(self, row) -> None:  # noqa: ANN001
            self.rows.append(row)

        def save(self, path: str) -> None:
            self.saved_path = path

    monkeypatch.setattr(analyze_module, "Workbook", _FakeWorkbook)
    monkeypatch.setattr(
        analyze_module,
        "load_config",
        lambda section=None, key=None: (
            {"excel_path": "static/excel"} if section == "files" else {}
        ),
    )

    created_at = datetime(2026, 1, 2, 3, 4, 5)
    spring = AsyncMock()
    spring.get_articles_for_excel_export.return_value = [
        {"id": 1, "title": "t", "create_at": created_at}
    ]
    service = _make_service(spring_client=spring)

    file_path = await service.export_articles_to_excel(MagicMock())

    workbook = created[0]
    assert workbook.rows[0] == [Messages.EXPORT_ARTICLES_EXCEL_TIP]
    assert workbook.rows[1][0] == "id"
    assert workbook.rows[2][0] == 1
    assert workbook.rows[2][6] == created_at.isoformat()
    assert workbook.saved_path == file_path
    assert file_path.endswith(Messages.EXPORT_ARTICLES_EXCEL_FILENAME)


# ===== 文章统计 =====


# 统计命中缓存时直接返回且不查询 ClickHouse
@pytest.mark.anyio
async def test_statistics_returns_cached_result() -> None:
    cached = {"total_views": 1}
    service = _make_service(statistics_cache=_fake_cache(return_value=cached))

    result = await service.get_article_statistics_service(MagicMock())

    assert result == cached
    service.articleMapper.get_platform_stats_clickhouse_mapper_async.assert_not_awaited()


# 统计优先取 ClickHouse 结果并写回缓存
@pytest.mark.anyio
async def test_statistics_prefers_clickhouse_and_caches() -> None:
    stats = {"total_views": 10, "total_articles": 2}
    mapper = AsyncMock()
    mapper.get_platform_stats_clickhouse_mapper_async = AsyncMock(return_value=stats)
    service = _make_service(articleMapper=mapper)

    result = await service.get_article_statistics_service(MagicMock())

    assert result == stats
    service._statistics_cache.set.assert_awaited_once_with(stats)
    service._spring_client.get_total_views.assert_not_awaited()


# ClickHouse 失败时并行调用 Spring 八项统计并按原键合并
@pytest.mark.anyio
async def test_statistics_degrades_to_parallel_spring_calls() -> None:
    mapper = AsyncMock()
    mapper.get_platform_stats_clickhouse_mapper_async = AsyncMock(
        side_effect=RuntimeError("ch down")
    )
    spring = AsyncMock()
    spring.get_total_views.return_value = ("total_views", 100)
    spring.get_total_articles.return_value = ("total_articles", 4)
    spring.get_active_authors.return_value = ("active_authors", 3)
    spring.get_average_views.return_value = ("average_views", {"value": 25})
    spring.get_total_likes.return_value = ("total_likes", 40)
    spring.get_average_likes.return_value = ("average_likes", {"value": 10})
    spring.get_total_collects.return_value = ("total_collects", 8)
    spring.get_average_collects.return_value = ("average_collects", {"value": 2})
    service = _make_service(articleMapper=mapper, spring_client=spring)

    result = await service.get_article_statistics_service(MagicMock())

    assert result == {
        "total_views": ("total_views", 100),
        "total_articles": ("total_articles", 4),
        "active_authors": ("active_authors", 3),
        "average_views": ("average_views", {"value": 25}),
        "total_likes": ("total_likes", 40),
        "average_likes": ("average_likes", {"value": 10}),
        "total_collects": ("total_collects", 8),
        "average_collects": ("average_collects", {"value": 2}),
    }
    for method in (
        spring.get_total_views,
        spring.get_total_articles,
        spring.get_active_authors,
        spring.get_average_views,
        spring.get_total_likes,
        spring.get_average_likes,
        spring.get_total_collects,
        spring.get_average_collects,
    ):
        method.assert_awaited_once()
    service._statistics_cache.set.assert_awaited_once_with(result)


# ===== 分类文章数 =====


# 分类文章数按 ClickHouse 结果降序排序并写回缓存
@pytest.mark.anyio
async def test_category_count_maps_clickhouse_and_sorts_desc() -> None:
    rows = [
        {"category_id": 1, "category_name": "A", "article_count": 2},
        {"category_id": 2, "category_name": "B", "article_count": 5},
    ]
    mapper = AsyncMock()
    mapper.get_category_article_count_clickhouse_mapper_async = AsyncMock(
        return_value=rows
    )
    service = _make_service(articleMapper=mapper)

    result = await service.get_category_article_count_service(MagicMock())

    assert [item["category_name"] for item in result] == ["B", "A"]
    assert result[0] == {"category_id": 2, "category_name": "B", "article_count": 5}
    service._category_cache.set.assert_awaited_once_with(result)


# ClickHouse 为空时按 Spring 子分类聚合到父分类并补零
@pytest.mark.anyio
async def test_category_count_aggregates_spring_parent_categories() -> None:
    mapper = AsyncMock()
    mapper.get_category_article_count_clickhouse_mapper_async = AsyncMock(
        return_value=[]
    )
    spring = AsyncMock()
    spring.get_category_article_count.return_value = [
        {"sub_category_id": 11, "count": 3}
    ]
    spring.get_all_categories.return_value = [
        {"id": 1, "name": "A"},
        {"id": 2, "name": "B"},
    ]
    spring.get_subcategories_with_parent.return_value = [{"id": 11, "category_id": 1}]
    service = _make_service(articleMapper=mapper, spring_client=spring)

    result = await service.get_category_article_count_service(MagicMock())

    assert result == [
        {"category_id": 1, "category_name": "A", "article_count": 3},
        {"category_id": 2, "category_name": "B", "article_count": 0},
    ]


# ClickHouse 查询异常时降级 Spring 聚合分类文章数
@pytest.mark.anyio
async def test_category_count_degrades_when_clickhouse_raises() -> None:
    mapper = AsyncMock()
    mapper.get_category_article_count_clickhouse_mapper_async = AsyncMock(
        side_effect=RuntimeError("ch down")
    )
    spring = AsyncMock()
    spring.get_category_article_count.return_value = [
        {"sub_category_id": 11, "count": 4}
    ]
    spring.get_all_categories.return_value = [{"id": 1, "name": "A"}]
    spring.get_subcategories_with_parent.return_value = [{"id": 11, "category_id": 1}]
    service = _make_service(articleMapper=mapper, spring_client=spring)

    result = await service.get_category_article_count_service(MagicMock())

    assert result == [{"category_id": 1, "category_name": "A", "article_count": 4}]
    spring.get_category_article_count.assert_awaited_once()


# ===== 月度发布数 =====


# 月度发布数补齐最近六个月并丢弃窗口外的月份
@pytest.mark.anyio
async def test_monthly_publish_fills_missing_months() -> None:
    current_month = datetime.now().strftime("%Y-%m")
    mapper = AsyncMock()
    mapper.get_monthly_publish_count_clickhouse_mapper_async = AsyncMock(
        return_value=[
            {"year_month": current_month, "count": 3},
            {"year_month": "1999-01", "count": 9},
        ]
    )
    service = _make_service(articleMapper=mapper)

    result = await service.get_monthly_publish_count_service(MagicMock())

    assert len(result) == 6
    months = [item["year_month"] for item in result]
    assert months == sorted(months)
    by_month = {item["year_month"]: item["count"] for item in result}
    assert by_month[current_month] == 3
    assert "1999-01" not in by_month


# ClickHouse 失败时降级 Spring 并返回六个月零值
@pytest.mark.anyio
async def test_monthly_publish_degrades_to_spring() -> None:
    mapper = AsyncMock()
    mapper.get_monthly_publish_count_clickhouse_mapper_async = AsyncMock(
        side_effect=RuntimeError("ch down")
    )
    spring = AsyncMock()
    spring.get_monthly_publish_count.return_value = []
    service = _make_service(articleMapper=mapper, spring_client=spring)

    result = await service.get_monthly_publish_count_service(MagicMock())

    assert len(result) == 6
    assert all(item["count"] == 0 for item in result)
    spring.get_monthly_publish_count.assert_awaited_once()

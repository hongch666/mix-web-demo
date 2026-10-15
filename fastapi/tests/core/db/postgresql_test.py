from collections.abc import Generator

import pytest

from app.core.db import (
    get_pgvector_connection_string,
    get_postgres_config,
    postgresql as postgresql_module,
)


@pytest.fixture(autouse=True)
def _clear_connection_string_cache() -> Generator[None, None, None]:
    """清掉连接串的 lru_cache，避免用例之间复用按旧配置生成的结果"""
    get_pgvector_connection_string.cache_clear()
    yield
    get_pgvector_connection_string.cache_clear()


# 以 database.postgres 段作为 PostgreSQL 配置来源
def test_get_postgres_config_reads_postgres_section(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        postgresql_module,
        "load_config",
        lambda section: {"postgres": {"host": "pg", "port": 5432}},
    )

    assert get_postgres_config() == {"host": "pg", "port": 5432}


# 按 psycopg2 格式拼装连接串，日志只记录目标库不泄露密码
def test_get_pgvector_connection_string_builds_psycopg2_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        postgresql_module,
        "load_config",
        lambda section: {
            "postgres": {
                "user": "vector",
                "password": "unit-test-secret",
                "host": "pg.internal",
                "port": 5432,
                "database": "warehouse",
            }
        },
    )
    logged: list[str] = []
    monkeypatch.setattr(postgresql_module.Logger, "info", logged.append)

    connection_string: str = get_pgvector_connection_string()

    assert connection_string == (
        "postgresql+psycopg2://vector:unit-test-secret@pg.internal:5432/warehouse"
    )
    assert len(logged) == 1
    assert "warehouse" in logged[0]
    assert "unit-test-secret" not in logged[0]


# 连接串带 lru_cache，重复获取只读取一次配置
def test_get_pgvector_connection_string_caches_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sections: list[str] = []

    def fake_load_config(section: str) -> dict[str, object]:
        sections.append(section)
        return {
            "postgres": {
                "user": "vector",
                "password": "unit-test-secret",
                "host": "pg",
                "port": 5432,
                "database": "warehouse",
            }
        }

    monkeypatch.setattr(postgresql_module, "load_config", fake_load_config)

    first: str = get_pgvector_connection_string()
    second: str = get_pgvector_connection_string()

    assert first == second
    assert sections == ["database"]


# 配置缺字段时向上抛错并记录失败日志，避免把残缺连接串交给 LangChain
def test_get_pgvector_connection_string_raises_on_incomplete_config(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        postgresql_module, "load_config", lambda section: {"postgres": {}}
    )
    errors: list[str] = []
    monkeypatch.setattr(postgresql_module.Logger, "error", errors.append)

    with pytest.raises(KeyError):
        get_pgvector_connection_string()

    assert len(errors) == 1

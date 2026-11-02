from .clickhouse import create_warehouse_indexes_async, create_warehouse_tables_async
from .mysql import create_mysql_indexes_async, create_tables_async
from .postgresql import ensure_pgvector_indexes_async


async def init_databases_async() -> None:
    """按依赖顺序初始化全部数据库：业务表与索引、数仓表与索引、向量索引"""

    # 每个存储都是先建表再补索引，表不存在时索引补建会直接跳过
    await create_tables_async()
    await create_mysql_indexes_async()
    await create_warehouse_tables_async()
    await create_warehouse_indexes_async()
    await ensure_pgvector_indexes_async()

from app.internal.schemas import (
    ChangeEventDTO,
    Neo4jSyncDTO,
    VectorSyncDTO,
    WarehouseSyncDTO,
)


# 事件 DTO 能解析 Spring 下发的事件负载
def test_vector_sync_dto_parses_spring_event() -> None:
    dto = VectorSyncDTO.model_validate(
        {
            "resource": "articles",
            "change_type": "update",
            "ids": [1, 2],
            "action": "edit",
            "trigger_user_id": 7,
            "trigger_username": "tester",
            "occurred_at": "2026-10-04T20:00:00",
        }
    )

    assert dto.resource == "articles"
    assert dto.change_type == "update"
    assert dto.ids == [1, 2]
    assert dto.trigger_user_id == 7


# Neo4j 同步请求能解析事件列表负载
def test_neo4j_sync_dto_parses_events_payload() -> None:
    dto = Neo4jSyncDTO.model_validate(
        {
            "events": [
                {
                    "resource": "likes",
                    "change_type": "delete",
                    "ids": [9],
                    "trigger_user_id": 3,
                }
            ]
        }
    )

    assert len(dto.events) == 1
    assert dto.events[0].resource == "likes"
    assert dto.events[0].change_type == "delete"
    assert dto.events[0].trigger_user_id == 3


# 数仓同步请求能解析资源列表负载
def test_warehouse_sync_dto_parses_resources_payload() -> None:
    dto = WarehouseSyncDTO.model_validate({"resources": ["comments", "likes"]})

    assert dto.resources == ["comments", "likes"]


# 缺失字段时使用安全默认值
def test_change_event_dto_defaults() -> None:
    dto = ChangeEventDTO.model_validate({})

    assert dto.resource == ""
    assert dto.change_type == ""
    assert dto.ids == []
    assert dto.trigger_user_id is None

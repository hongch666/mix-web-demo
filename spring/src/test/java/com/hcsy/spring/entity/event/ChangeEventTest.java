package com.hcsy.spring.entity.event;

import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.List;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import com.hcsy.spring.common.constants.SyncChangeType;
import com.hcsy.spring.common.constants.SyncResource;

import com.fasterxml.jackson.databind.ObjectMapper;

class ChangeEventTest {

    private final ObjectMapper objectMapper = new ObjectMapper();

    @Test
    @DisplayName("事件序列化为下划线字段，保证下游 GoZero 与 FastAPI 可解析")
    void serializesSnakeCaseFields() throws Exception {
        ChangeEvent event = ChangeEvent.of(SyncResource.ARTICLES, SyncChangeType.UPDATE, List.of(1L, 2L), "edit");
        event.setTriggerUserId(7L);
        event.setTriggerUsername("tester");

        String json = objectMapper.writeValueAsString(event);

        assertTrue(json.contains("\"resource\":\"articles\""));
        assertTrue(json.contains("\"change_type\":\"update\""));
        assertTrue(json.contains("\"ids\":[1,2]"));
        assertTrue(json.contains("\"trigger_user_id\":7"));
        assertTrue(json.contains("\"trigger_username\":\"tester\""));
    }

    @Test
    @DisplayName("变更类型由操作类型推导，删除与新增语义正确")
    void resolvesChangeTypeFromAction() {
        assertTrue(SyncChangeType.fromAction("add") == SyncChangeType.INSERT);
        assertTrue(SyncChangeType.fromAction("like") == SyncChangeType.INSERT);
        assertTrue(SyncChangeType.fromAction("edit") == SyncChangeType.UPDATE);
        assertTrue(SyncChangeType.fromAction("publish") == SyncChangeType.UPDATE);
        assertTrue(SyncChangeType.fromAction("delete") == SyncChangeType.DELETE);
        assertTrue(SyncChangeType.fromAction("unlike") == SyncChangeType.DELETE);
    }
}

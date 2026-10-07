package com.hcsy.spring.common.utils;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.List;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import com.hcsy.spring.common.constants.SyncChangeType;
import com.hcsy.spring.entity.event.ChangeEvent;

class SyncEventCollectorTest {

    static class SampleDto {
        private final Long id;
        private final String title;

        SampleDto(Long id, String title) {
            this.id = id;
            this.title = title;
        }

        public Long getId() {
            return id;
        }

        public String getTitle() {
            return title;
        }
    }

    // 验证该场景的预期行为
    @Test
    @DisplayName("构建变更事件写入资源、变更类型与解析出的主键")
    void collectBuildsChangeEvent() {
        ChangeEvent event = SyncEventCollector.collect("article", SyncChangeType.INSERT, 9L, null);

        assertEquals("article", event.getResource());
        assertEquals(SyncChangeType.INSERT.value(), event.getChangeType());
        assertEquals(List.of(9L), event.getIds());
        assertEquals("", event.getAction());
        assertNotNull(event.getOccurredAt());
    }

    // 验证该场景的预期行为
    @Test
    @DisplayName("新增场景优先取返回值主键，返回值无主键时退回入参")
    void resolveIdsPrefersResultThenParamForInsert() {
        assertEquals(List.of(7L),
            SyncEventCollector.resolveIds(SyncChangeType.INSERT, 3L, Result.success(new SampleDto(7L, "标题"))));
        assertEquals(List.of(3L),
            SyncEventCollector.resolveIds(SyncChangeType.INSERT, 3L, Result.success(null)));
    }

    // 验证该场景的预期行为
    @Test
    @DisplayName("更新场景直接取入参主键，入参与返回值都解析不到时返回空集合")
    void resolveIdsUsesParamForUpdate() {
        assertEquals(List.of(5L, 6L),
            SyncEventCollector.resolveIds(SyncChangeType.UPDATE, "5,6", Result.success(9L)));
        assertTrue(SyncEventCollector.resolveIds(SyncChangeType.UPDATE, null, Result.success(null)).isEmpty());
    }

    // 验证该场景的预期行为
    @Test
    @DisplayName("非统一响应结果与空 data 都解析不出主键")
    void readIdsFromResultRequiresBusinessResult() {
        assertTrue(SyncEventCollector.readIdsFromResult("5").isEmpty());
        assertTrue(SyncEventCollector.readIdsFromResult(Result.success(null)).isEmpty());
        assertEquals(List.of(12L), SyncEventCollector.readIdsFromResult(Result.success(12L)));
    }

    // 验证该场景的预期行为
    @Test
    @DisplayName("主键兼容单个数字、集合与逗号分隔字符串并过滤非法项")
    void readIdsSupportsNumberCollectionAndCsv() {
        assertEquals(List.of(7L), SyncEventCollector.readIds(7));
        assertEquals(List.of(1L, 2L), SyncEventCollector.readIds(List.of(1L, "非法", 2)));
        assertEquals(List.of(5L, 6L), SyncEventCollector.readIds(" 5,6 ,abc, "));
        assertEquals(List.of(), SyncEventCollector.readIds(List.of("非法")));
    }

    // 验证该场景的预期行为
    @Test
    @DisplayName("空值与空白字符串解析为空集合")
    void readIdsReturnsEmptyForBlankOrNull() {
        assertTrue(SyncEventCollector.readIds(null).isEmpty());
        assertTrue(SyncEventCollector.readIds("").isEmpty());
        assertTrue(SyncEventCollector.readIds("   ").isEmpty());
    }

    // 验证该场景的预期行为
    @Test
    @DisplayName("对象主键按 id 属性读取，缺少该属性时返回空集合")
    void readIdsReadsIdProperty() {
        assertEquals(List.of(11L), SyncEventCollector.readIds(new SampleDto(11L, "标题")));
        assertTrue(SyncEventCollector.readIds(new Object()).isEmpty());
    }

    // 验证该场景的预期行为
    @Test
    @DisplayName("属性读取按 getter 取值，getter 缺失与目标为空时返回 null")
    void readPropertyHandlesMissingGetter() {
        SampleDto dto = new SampleDto(11L, "标题");

        assertEquals(11L, SyncEventCollector.readProperty(dto, "id"));
        assertNull(SyncEventCollector.readProperty(dto, "missing"));
        assertNull(SyncEventCollector.readProperty(null, "id"));
    }

    // 验证该场景的预期行为
    @Test
    @DisplayName("按属性读取 Long 与 String 时做类型判断")
    void readLongAndReadStringCheckType() {
        SampleDto dto = new SampleDto(11L, "标题");

        assertEquals(11L, SyncEventCollector.readLong(dto, "id"));
        assertNull(SyncEventCollector.readLong(dto, "title"));
        assertEquals("标题", SyncEventCollector.readString(dto, "title"));
        assertNull(SyncEventCollector.readString(dto, "id"));
    }

    // 验证该场景的预期行为
    @Test
    @DisplayName("按参数名解析 Long 型入参，参数名或参数值缺失时返回 null")
    void readByNameResolvesParameterValue() {
        String[] parameterNames = { "userId", "focusId" };
        Object[] parameterValues = { 1L, 2L };

        assertEquals(2L, SyncEventCollector.readByName(parameterNames, parameterValues, "focusId"));
        assertEquals(1L, SyncEventCollector.readByName(parameterNames, parameterValues, "userId"));
        assertNull(SyncEventCollector.readByName(parameterNames, parameterValues, "articleId"));
        assertNull(SyncEventCollector.readByName(null, parameterValues, "focusId"));
        assertNull(SyncEventCollector.readByName(parameterNames, null, "focusId"));
        assertNull(SyncEventCollector.readByName(new String[] { "focusId" }, new Object[] { "2" }, "focusId"));
        assertNull(SyncEventCollector.readByName(parameterNames, new Object[] { 1L }, "focusId"));
    }
}

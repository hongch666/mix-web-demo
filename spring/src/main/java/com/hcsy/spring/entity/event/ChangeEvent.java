package com.hcsy.spring.entity.event;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.List;

import com.hcsy.spring.common.constants.SyncChangeType;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 数据变更事件
 * 由同步切面采集后下发到 ES、向量库、Neo4j 与数仓，携带表名、主键与变更类型
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ChangeEvent {

    private static final DateTimeFormatter TIME_FORMATTER = DateTimeFormatter.ISO_LOCAL_DATE_TIME;

    /** 资源名，见 SyncResource */
    private String resource;

    /** 变更类型，见 SyncChangeType 的 value */
    @JsonProperty("change_type")
    private String changeType;

    /** 受影响的主键集合，为空时下游退化为全量同步 */
    private List<Long> ids;

    /** 原始操作类型，用于日志与下游细分 */
    private String action;

    /** 触发本次变更的用户 ID，关系类资源用于定位关系一端 */
    @JsonProperty("trigger_user_id")
    private Long triggerUserId;

    /** 触发本次变更的用户名 */
    @JsonProperty("trigger_username")
    private String triggerUsername;

    /** 事件产生时间，用于下游乱序丢弃 */
    @JsonProperty("occurred_at")
    private String occurredAt;

    public static ChangeEvent of(String resource, SyncChangeType changeType, List<Long> ids, String action) {
        return ChangeEvent.builder()
            .resource(resource)
            .changeType(changeType.value())
            .ids(ids == null ? List.of() : ids)
            .action(action)
            .occurredAt(LocalDateTime.now().format(TIME_FORMATTER))
            .build();
    }

    public boolean isEmptyIds() {
        return ids == null || ids.isEmpty();
    }
}

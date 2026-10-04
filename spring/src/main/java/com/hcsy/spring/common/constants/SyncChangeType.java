package com.hcsy.spring.common.constants;

/**
 * 数据变更类型
 * 用于精确同步时描述源表记录的变更方式
 */
public enum SyncChangeType {

    INSERT("insert"), UPDATE("update"), DELETE("delete");

    private final String value;

    SyncChangeType(String value) {
        this.value = value;
    }

    public String value() {
        return value;
    }

    /**
     * 根据文章操作类型推导变更类型
     * 点赞、收藏、关注等关系类新增为 INSERT，取消除外；浏览与发布为 UPDATE；新增为 INSERT
     */
    public static SyncChangeType fromAction(String action) {
        if (action == null) {
            return UPDATE;
        }
        return switch (action) {
            case "add", "like", "collect", "focus" -> INSERT;
            case "delete", "unlike", "uncollect", "unfocus" -> DELETE;
            default -> UPDATE;
        };
    }
}

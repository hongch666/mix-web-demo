package com.hcsy.spring.common.constants;

/**
 * 数据变更类型
 * 用于精确同步时描述源表记录的变更方式
 */
public enum SyncChangeType {

    INSERT("insert"), UPDATE("update"), DELETE("delete");

    private final String value;

    /**
     * 枚举构造器，绑定变更类型字符串值
     */
    SyncChangeType(String value) {
        this.value = value;
    }

    /**
     * 返回下发到下游的变更类型字符串值
     */
    public String value() {
        return value;
    }

    /**
     * 根据文章操作类型推导变更类型
     * 点赞、收藏、关注等关系类新增为 INSERT，取消除外；浏览与发布为 UPDATE；新增为 INSERT
     */
    public static SyncChangeType fromAction(SyncAction action) {
        if (action == null) {
            return UPDATE;
        }
        return switch (action) {
            case ADD, LIKE, COLLECT, FOCUS -> INSERT;
            case DELETE, UNLIKE, UNCOLLECT, UNFOCUS -> DELETE;
            default -> UPDATE;
        };
    }
}

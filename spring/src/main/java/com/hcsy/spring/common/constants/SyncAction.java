package com.hcsy.spring.common.constants;

import com.fasterxml.jackson.annotation.JsonValue;

/**
 * 文章同步操作类型
 * 取值与下游 NestJS 文章日志消费者、数仓与图谱同步链路约定的字符串保持一致
 */
public enum SyncAction {

    ADD("add"), EDIT("edit"), DELETE("delete"), PUBLISH("publish"), VIEW("view"), LIKE("like"), UNLIKE(
        "unlike"), COLLECT("collect"), UNCOLLECT("uncollect"), FOCUS("focus"), UNFOCUS("unfocus");

    private final String value;

    /**
     * 枚举构造器，绑定下发到消息队列与下游的字符串值
     */
    SyncAction(String value) {
        this.value = value;
    }

    // ===== 同步动作取值 =====

    /**
     * 下发到消息队列与下游的字符串值
     */
    @JsonValue
    public String value() {
        return value;
    }
}

package com.hcsy.spring.entity.event;

import java.util.Map;

import com.fasterxml.jackson.annotation.JsonInclude;
import lombok.Builder;
import lombok.Data;

/**
 * 接口日志事件
 * 由日志切面构建后投递到 api-log-queue，字段名与 NestJS 消费者约定保持一致
 */
@Data
@Builder
@JsonInclude(JsonInclude.Include.NON_NULL)
public class ApiLogEvent {

    /** 发起请求的用户 ID，未登录为 0 */
    private Long userId;

    /** 发起请求的用户名，未登录为 unknown */
    private String username;

    /** 接口描述，取自 @ApiLog 的 value */
    private String apiDescription;

    /** 接口路径，形如 /articles/{id} */
    private String apiPath;

    /** HTTP 方法 */
    private String apiMethod;

    /** 路径参数，键为参数名，结构由接口决定 */
    private Map<String, Object> pathParams;

    /** 请求体，键由请求 DTO 决定，敏感字段已在切面中剔除 */
    private Object requestBody;

    /** 接口耗时，单位毫秒 */
    private long responseTime;
}

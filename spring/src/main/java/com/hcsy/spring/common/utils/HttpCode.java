package com.hcsy.spring.common.utils;

/**
 * HTTP状态码常量类
 */
public class HttpCode {

    // 成功
    public static final int OK = 200;

    // 请求参数错误
    public static final int BAD_REQUEST = 400;

    // 未认证/未登录
    public static final int UNAUTHORIZED = 401;

    // 无权限/禁止访问
    public static final int FORBIDDEN = 403;

    // 资源不存在
    public static final int NOT_FOUND = 404;

    // 资源冲突
    public static final int CONFLICT = 409;

    // 请求格式正确但语义错误/无法处理
    public static final int UNPROCESSABLE_ENTITY = 422;

    // 服务器内部错误
    public static final int INTERNAL_SERVER_ERROR = 500;

    // 服务不可用
    public static final int SERVICE_UNAVAILABLE = 503;

    private HttpCode() {
    }
}

package com.hcsy.spring.common.utils;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class Result {
    private Integer code; // 响应码，HTTP状态码
    private String msg; // 响应信息 描述字符串
    private Object data; // 返回的数据

    // 增删改 成功响应
    public static Result success() {
        return new Result(HttpCode.OK, "success", null);
    }

    // 查询 成功响应
    public static Result success(Object data) {
        return new Result(HttpCode.OK, "success", data);
    }

    // 失败响应（默认500）
    public static Result error(String msg) {
        return new Result(HttpCode.INTERNAL_SERVER_ERROR, msg, null);
    }

    // 失败响应（指定HTTP状态码）
    public static Result error(int code, String msg) {
        return new Result(code, msg, null);
    }
}

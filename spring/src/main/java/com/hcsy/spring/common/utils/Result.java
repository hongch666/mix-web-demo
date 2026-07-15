package com.hcsy.spring.common.utils;

import com.hcsy.spring.common.constants.HttpCode;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 统一响应结果封装（泛型版本）
 *
 * @param <T> data 的数据类型
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class Result<T> {
    private Integer code; // 响应码，HTTP状态码
    private String msg; // 响应信息 描述字符串
    private T data; // 返回的数据

    // 增删改 成功响应
    public static <T> Result<T> success() {
        return new Result<>(HttpCode.OK, "success", null);
    }

    // 查询 成功响应
    public static <T> Result<T> success(T data) {
        return new Result<>(HttpCode.OK, "success", data);
    }

    // 失败响应（默认500）
    public static <T> Result<T> error(String msg) {
        return new Result<>(HttpCode.INTERNAL_SERVER_ERROR, msg, null);
    }

    // 失败响应（指定HTTP状态码）
    public static <T> Result<T> error(int code, String msg) {
        return new Result<>(code, msg, null);
    }
}

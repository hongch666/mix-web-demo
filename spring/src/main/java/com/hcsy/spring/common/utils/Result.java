package com.hcsy.spring.common.utils;

import com.hcsy.spring.common.constants.HttpCode;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 统一响应结果封装（泛型版本）
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@Schema(description = "统一响应")
public class Result<T> {
    @Schema(description = "响应码")
    private Integer code;

    @Schema(description = "响应信息")
    private String msg;

    @Schema(description = "返回数据")
    private T data;

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

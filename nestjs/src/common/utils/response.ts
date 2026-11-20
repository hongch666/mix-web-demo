import { HttpCode } from "../constants";
import type { ApiResponse } from "../interfaces/apiResponse.interface";

// 类型定义在 common/interfaces 下，这里保留转发入口，调用方仍可从响应工具导入
export type { ApiResponse };

/**
 * 构造 code 为 200 的成功响应体
 */
export function success<T>(data: T, msg = "success"): ApiResponse<T> {
  return {
    code: HttpCode.OK,
    msg,
    data,
  };
}

/**
 * 按指定状态码构造 data 为空的失败响应体
 */
export function error(code: number, msg = "failed"): ApiResponse<null> {
  return {
    code,
    msg,
    data: null,
  };
}

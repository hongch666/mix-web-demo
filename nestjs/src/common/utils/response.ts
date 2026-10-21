import { HttpCode } from "../constants";

/**
 * 统一接口响应体结构，code 与 HTTP 状态码一致，msg 为提示信息，data 为成功时的业务数据
 */
export interface ApiResponse<T = unknown> {
  code: number; // 3 位 HTTP 状态码，与 HTTP 响应状态码一致
  msg: string; // 提示信息
  data?: T; // 成功时返回数据
}

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

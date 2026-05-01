import { HttpCode } from './httpCode';

export interface ApiResponse<T = any> {
  code: number; // 3 位 HTTP 状态码，与 HTTP 响应状态码一致
  msg: string; // 提示信息
  data?: T; // 成功时返回数据
}

export function success<T>(data: T, msg = 'success'): ApiResponse<T> {
  return {
    code: HttpCode.OK,
    msg,
    data,
  };
}

export function error(code: number, msg = 'failed'): ApiResponse<null> {
  return {
    code,
    msg,
    data: null,
  };
}

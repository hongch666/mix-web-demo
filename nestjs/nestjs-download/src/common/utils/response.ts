// src/common/utils/response.ts

export interface ApiResponse<T = any> {
  code: number;      // 1 表示成功，0为错误码
  msg: string;   // 提示信息
  data?: T;          // 成功时返回数据
}

export function success<T>(data: T, msg = 'success'): ApiResponse<T> {
  return {
    code: 1,
    msg,
    data,
  };
}

export function error(msg = 'failed'): ApiResponse<null> {
  return {
    code: 0,
    msg,
    data: null,
  };
}

/**
 * 统一接口响应体结构，code 与 HTTP 状态码一致，msg 为提示信息，data 为成功时的业务数据
 *
 * 所有控制器与远程调用响应都复用该结构，构造与解包函数见 `common/utils/response.ts`
 */
export interface ApiResponse<T = unknown> {
  /** 3 位 HTTP 状态码，与 HTTP 响应状态码一致 */
  code: number;
  /** 提示信息 */
  msg: string;
  /** 成功时返回数据 */
  data?: T;
}

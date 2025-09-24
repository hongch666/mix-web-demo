import { applyDecorators, UseInterceptors } from '@nestjs/common';
import { ApiLog, ApiLogOptions } from './api-log.decorator';
import { ApiLogInterceptor } from '../interceptors/api-log.interceptor';

/**
 * 组合装饰器：同时应用 @ApiLog 和 @UseInterceptors(ApiLogInterceptor)
 * 如果已经在全局注册了 ApiLogInterceptor，则只需要使用 @ApiLog 即可
 * @param options 日志配置选项
 */
export const MethodLog = (options: ApiLogOptions | string) => {
  return applyDecorators(ApiLog(options), UseInterceptors(ApiLogInterceptor));
};

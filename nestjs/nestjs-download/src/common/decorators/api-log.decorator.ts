import { SetMetadata } from '@nestjs/common';

export const API_LOG_KEY = 'api_log';

export interface ApiLogOptions {
  message: string; // 日志消息
  includeParams?: boolean; // 是否包含参数，默认true
  logLevel?: 'info' | 'warn' | 'error'; // 日志级别，默认info
  excludeFields?: string[]; // 排除的字段
}

/**
 * API日志装饰器
 * @param options 日志配置选项，可以是字符串（消息）或配置对象
 * @example
 * @ApiLog('新增日志')
 * @ApiLog({ message: '查询日志', includeParams: true, logLevel: 'info' })
 */
export const ApiLog = (options: ApiLogOptions | string) => {
  // 如果传入的是字符串，转换为配置对象
  const config: ApiLogOptions =
    typeof options === 'string'
      ? { message: options, includeParams: true, logLevel: 'info' }
      : { includeParams: true, logLevel: 'info', ...options };

  return SetMetadata(API_LOG_KEY, config);
};

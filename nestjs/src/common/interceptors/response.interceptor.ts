import {
  Injectable,
  NestInterceptor,
  ExecutionContext,
  CallHandler,
} from '@nestjs/common';
import { Observable, map } from 'rxjs';
import { success, ApiResponse } from '../utils/response';

@Injectable()
export class ResponseInterceptor<T> implements NestInterceptor<T, any> {
  /**
   * 判断是否已经是标准的 ApiResponse 格式
   * @param data 返回的数据
   * @returns 是否已经是标准格式
   */
  private isApiResponse(data: any): data is ApiResponse {
    return (
      data &&
      typeof data === 'object' &&
      'code' in data &&
      'msg' in data &&
      typeof data.code === 'number'
    );
  }

  intercept(context: ExecutionContext, next: CallHandler<T>): Observable<any> {
    return next.handle().pipe(
      map((data) => {
        // 如果已经是 ApiResponse 格式（success 或 error 返回的对象），直接返回
        if (this.isApiResponse(data)) {
          return data;
        }

        // 否则自动包装成 success 格式
        return success(data);
      }),
    );
  }
}

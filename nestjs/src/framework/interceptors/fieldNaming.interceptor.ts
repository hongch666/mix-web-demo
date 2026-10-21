import {
  CallHandler,
  ExecutionContext,
  Injectable,
  NestInterceptor,
} from "@nestjs/common";
import { Observable } from "rxjs";
import { map } from "rxjs/operators";

type JsonValue =
  | string
  | number
  | boolean
  | null
  | JsonValue[]
  | { [key: string]: JsonValue };

/**
 * 判断值是否为普通对象（原型为 Object.prototype 或 null），用于限定递归转换范围
 */
function isPlainObject(value: unknown): value is Record<string, unknown> {
  if (value === null || typeof value !== "object") {
    return false;
  }

  const prototype = Object.getPrototypeOf(value);
  return prototype === Object.prototype || prototype === null;
}

/**
 * 将驼峰命名的键名转换为下划线命名
 */
function toSnakeCase(key: string): string {
  return key.replace(/[A-Z]/g, (letter: string) => `_${letter.toLowerCase()}`);
}

/**
 * 动态 JSON 数据容器：这些字段的值是业务数据本身，内部键由写入方决定而非接口契约，
 * 不参与对外命名转换，否则同一份数据在 MongoDB（驼峰）与数仓（下划线）会落成两套键名
 */
const RAW_VALUE_KEYS: ReadonlySet<string> = new Set(["content"]);

/**
 * 递归转换 JSON 数据的对象键，content 等原始数据容器的内部键保持原样不参与命名转换
 */
function convertKeys(
  value: unknown,
  converter: (key: string) => string,
): unknown {
  if (Array.isArray(value)) {
    return value.map((item: unknown) => convertKeys(item, converter));
  }

  if (!isPlainObject(value)) {
    return value;
  }

  const result: Record<string, unknown> = {};
  for (const [key, item] of Object.entries(value)) {
    result[converter(key)] = RAW_VALUE_KEYS.has(key)
      ? item
      : convertKeys(item, converter);
  }
  return result;
}

/**
 * 对外字段命名转换拦截器，在 createApp 中全局注册，使响应字段以下划线风格输出以匹配前端契约
 */
@Injectable()
export class FieldNamingInterceptor implements NestInterceptor {
  /**
   * 将响应数据中的对象键从驼峰统一转换为下划线命名后返回给客户端
   */
  intercept(
    context: ExecutionContext,
    next: CallHandler,
  ): Observable<JsonValue> {
    return next
      .handle()
      .pipe(
        map((data: unknown) => convertKeys(data, toSnakeCase) as JsonValue),
      );
  }
}

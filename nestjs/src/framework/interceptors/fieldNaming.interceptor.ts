import {
  CallHandler,
  ExecutionContext,
  Injectable,
  NestInterceptor,
} from '@nestjs/common';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';

type JsonValue =
  | string
  | number
  | boolean
  | null
  | JsonValue[]
  | { [key: string]: JsonValue };

function isPlainObject(value: unknown): value is Record<string, unknown> {
  if (value === null || typeof value !== 'object') {
    return false;
  }

  const prototype = Object.getPrototypeOf(value);
  return prototype === Object.prototype || prototype === null;
}

function toSnakeCase(key: string): string {
  return key.replace(/[A-Z]/g, (letter: string) => `_${letter.toLowerCase()}`);
}

function convertKeys(value: unknown, converter: (key: string) => string): unknown {
  if (Array.isArray(value)) {
    return value.map((item: unknown) => convertKeys(item, converter));
  }

  if (!isPlainObject(value)) {
    return value;
  }

  const result: Record<string, unknown> = {};
  for (const [key, item] of Object.entries(value)) {
    result[converter(key)] = convertKeys(item, converter);
  }
  return result;
}

@Injectable()
export class FieldNamingInterceptor implements NestInterceptor {
  intercept(context: ExecutionContext, next: CallHandler): Observable<JsonValue> {
    return next
      .handle()
      .pipe(map((data: unknown) => convertKeys(data, toSnakeCase) as JsonValue));
  }
}

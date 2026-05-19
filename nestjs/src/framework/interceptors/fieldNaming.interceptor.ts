import {
  CallHandler,
  ExecutionContext,
  Injectable,
  NestInterceptor,
} from '@nestjs/common';
import type { FastifyRequest } from 'fastify';
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

function toCamelCase(key: string): string {
  return key.replace(/_([a-zA-Z0-9])/g, (_, letter: string) =>
    letter.toUpperCase(),
  );
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

function assignConvertedRequestField(
  request: FastifyRequest,
  field: 'body' | 'query' | 'params',
): void {
  const value = request[field];
  if (!isPlainObject(value) && !Array.isArray(value)) {
    return;
  }

  Object.defineProperty(request, field, {
    value: convertKeys(value, toCamelCase),
    writable: true,
    enumerable: true,
    configurable: true,
  });
}

@Injectable()
export class FieldNamingInterceptor implements NestInterceptor {
  intercept(context: ExecutionContext, next: CallHandler): Observable<JsonValue> {
    const request = context.switchToHttp().getRequest<FastifyRequest>();
    assignConvertedRequestField(request, 'body');
    assignConvertedRequestField(request, 'query');
    assignConvertedRequestField(request, 'params');

    return next
      .handle()
      .pipe(map((data: unknown) => convertKeys(data, toSnakeCase) as JsonValue));
  }
}

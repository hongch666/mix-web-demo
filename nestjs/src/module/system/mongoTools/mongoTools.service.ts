import { Injectable } from "@nestjs/common";
import { InjectConnection } from "@nestjs/mongoose";
import type { Connection } from "mongoose/types/connection";
import { ErrorIds, HttpCode, Messages } from "src/common/constants";
import { BusinessException } from "src/common/exceptions/business.exception";

// 允许查询的 collection 白名单，仅开放日志相关集合
const ALLOWED_COLLECTIONS = new Set<string>(["apilogs", "articlelogs"]);

// 禁止使用的 MongoDB 危险操作符，防止任意代码执行或高开销查询
const FORBIDDEN_OPERATORS = new Set<string>([
  "$where",
  "$function",
  "$accumulator",
  "$expr",
]);

interface MongoCollectionInfo {
  name: string;
  document_count: number;
  sample_fields: string[];
}

/**
 * MongoDB 工具服务，提供受限的日志查询能力（供 FastAPI 内部远程调用）
 * 仅允许读取白名单内的 collection，且仅支持只读 find 查询
 */
@Injectable()
export class MongoToolsService {
  constructor(@InjectConnection() private readonly connection: Connection) {}

  /**
   * 列出白名单内所有 collection 及其基本信息
   */
  async listCollections(): Promise<MongoCollectionInfo[]> {
    const infos: MongoCollectionInfo[] = [];
    const collections = await this.connection.db!.listCollections().toArray();

    for (const col of collections) {
      if (!ALLOWED_COLLECTIONS.has(col.name)) {
        continue;
      }
      const collection = this.connection.db!.collection(col.name);
      const documentCount = await collection.countDocuments({});
      const sample = await collection.findOne({});
      const sampleFields = sample ? Object.keys(sample).slice(0, 10) : [];
      infos.push({
        name: col.name,
        document_count: documentCount,
        sample_fields: sampleFields,
      });
    }

    return infos;
  }

  /**
   * 查询指定 collection 的文档（仅只读 find，且过滤危险操作符）
   * @param collectionName 集合名称（白名单内）
   * @param filter 查询过滤条件
   * @param limit 返回条数上限
   */
  async query(
    collectionName: string,
    filter: Record<string, unknown>,
    limit: number,
  ): Promise<unknown[]> {
    if (!ALLOWED_COLLECTIONS.has(collectionName)) {
      throw new BusinessException(
        Messages.MONGO_COLLECTION_NOT_ALLOWED_MSG(collectionName),
        HttpCode.BAD_REQUEST,
        ErrorIds.MONGO_COLLECTION_NOT_ALLOWED,
      );
    }

    this.assertSafeFilter(filter);

    const collection = this.connection.db!.collection(collectionName);
    const docs = await collection
      .find(filter ?? {})
      .limit(limit)
      .toArray();

    return docs.map((doc) => sanitizeDocument(doc));
  }

  /**
   * 校验过滤条件中不包含危险操作符
   */
  private assertSafeFilter(filter: Record<string, unknown>): void {
    const check = (obj: unknown): void => {
      if (Array.isArray(obj)) {
        obj.forEach(check);
        return;
      }
      if (obj !== null && typeof obj === "object") {
        for (const [key, value] of Object.entries(
          obj as Record<string, unknown>,
        )) {
          if (key.startsWith("$") && FORBIDDEN_OPERATORS.has(key)) {
            throw new BusinessException(
              Messages.MONGO_FORBIDDEN_OPERATOR_MSG(key),
              HttpCode.BAD_REQUEST,
              ErrorIds.MONGO_FORBIDDEN_OPERATOR,
            );
          }
          check(value);
        }
      }
    };
    check(filter);
  }
}

/**
 * 递归将 BSON 特殊类型转换为可 JSON 序列化的值
 */
function sanitizeDocument(value: unknown): unknown {
  if (value === null || value === undefined) {
    return value;
  }
  // BSON ObjectId 转十六进制字符串
  if (
    typeof value === "object" &&
    "_bsontype" in value &&
    (value as { _bsontype: string })._bsontype === "ObjectId"
  ) {
    return (value as { toString: () => string }).toString();
  }
  if (value instanceof Date) {
    return value.toISOString();
  }
  if (Buffer.isBuffer(value)) {
    return value.toString("base64");
  }
  if (Array.isArray(value)) {
    return value.map(sanitizeDocument);
  }
  if (typeof value === "object") {
    const result: Record<string, unknown> = {};
    for (const [key, item] of Object.entries(
      value as Record<string, unknown>,
    )) {
      result[key] = sanitizeDocument(item);
    }
    return result;
  }
  return value;
}

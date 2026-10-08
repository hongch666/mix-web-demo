import { Injectable } from "@nestjs/common";
import { InjectConnection } from "@nestjs/mongoose";
import type { Connection } from "mongoose";
import { ErrorIds, HttpCode, Messages, MongoTools } from "src/common/constants";
import { BusinessException } from "src/common/exceptions/business.exception";

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
    const collections = await this.connection.db!.listCollections().toArray();
    const allowedCollections = collections.filter((col) =>
      MongoTools.ALLOWED_COLLECTIONS.has(col.name),
    );

    const infos = await Promise.all(
      allowedCollections.map(async (col) => {
        const collection = this.connection.db!.collection(col.name);
        const [documentCount, sample] = await Promise.all([
          collection.countDocuments({}),
          collection.findOne({}),
        ]);
        return {
          name: col.name,
          document_count: documentCount,
          sample_fields: sample ? Object.keys(sample).slice(0, 10) : [],
        };
      }),
    );

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
    if (!MongoTools.ALLOWED_COLLECTIONS.has(collectionName)) {
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
   * 对白名单内的日志集合执行只读聚合管道
   *
   * 阶段白名单之外的阶段、形状非法的阶段与危险操作符都会被拒绝；
   * 结果条数由服务端强制收敛，并限制单次聚合的最长执行时间
   * @param collectionName 集合名称（白名单内）
   * @param pipeline 聚合管道
   * @param limit 结果返回条数上限
   */
  async aggregate(
    collectionName: string,
    pipeline: Record<string, unknown>[],
    limit: number,
  ): Promise<unknown[]> {
    if (!MongoTools.ALLOWED_COLLECTIONS.has(collectionName)) {
      throw new BusinessException(
        Messages.MONGO_COLLECTION_NOT_ALLOWED_MSG(collectionName),
        HttpCode.BAD_REQUEST,
        ErrorIds.MONGO_COLLECTION_NOT_ALLOWED,
      );
    }

    const safeLimit: number = Math.min(
      Math.max(Math.trunc(limit), 1),
      MongoTools.MAX_AGGREGATE_DOCS,
    );
    const safePipeline: Record<string, unknown>[] = this.buildSafePipeline(
      pipeline,
      safeLimit,
    );

    const collection = this.connection.db!.collection(collectionName);
    const docs = await collection
      .aggregate(safePipeline, {
        allowDiskUse: false,
        maxTimeMS: MongoTools.AGGREGATE_MAX_TIME_MS,
      })
      .toArray();

    return docs.map((doc) => sanitizeDocument(doc));
  }

  /**
   * 校验聚合管道并收敛结果条数
   *
   * 每个阶段必须是单操作符对象且在阶段白名单内，$limit 阶段统一收紧到上限，
   * 管道末尾缺少 $limit 时自动追加，保证聚合结果不会无限膨胀
   */
  private buildSafePipeline(
    pipeline: Record<string, unknown>[],
    safeLimit: number,
  ): Record<string, unknown>[] {
    if (!Array.isArray(pipeline) || pipeline.length === 0) {
      throw new BusinessException(
        Messages.MONGO_AGGREGATE_PIPELINE_EMPTY,
        HttpCode.BAD_REQUEST,
        ErrorIds.PARAM_PARSE_FAILED,
      );
    }
    if (pipeline.length > MongoTools.MAX_PIPELINE_STAGES) {
      throw new BusinessException(
        Messages.MONGO_AGGREGATE_PIPELINE_TOO_LONG_MSG(
          MongoTools.MAX_PIPELINE_STAGES,
        ),
        HttpCode.BAD_REQUEST,
        ErrorIds.PARAM_PARSE_FAILED,
      );
    }

    const safePipeline: Record<string, unknown>[] = pipeline.map(
      (stage: Record<string, unknown>, index: number) => {
        const [stageName, stageValue] = this.assertSafeStage(stage, index + 1);

        // 危险操作符可能藏在任意阶段内部，逐个阶段递归校验
        this.assertSafeFilter(stage);

        if (stageName === "$limit") {
          return { $limit: this.resolveStageLimit(stageValue, safeLimit) };
        }
        return { [stageName]: stageValue };
      },
    );

    const lastStage = safePipeline[safePipeline.length - 1];
    if (!Object.prototype.hasOwnProperty.call(lastStage, "$limit")) {
      safePipeline.push({ $limit: safeLimit });
    }

    return safePipeline;
  }

  /**
   * 校验单个聚合阶段的形状与白名单，返回阶段名与阶段值
   * @param stage 聚合阶段
   * @param position 阶段序号（从 1 开始），便于调用方定位问题阶段
   */
  private assertSafeStage(
    stage: Record<string, unknown>,
    position: number,
  ): [string, unknown] {
    if (stage === null || typeof stage !== "object" || Array.isArray(stage)) {
      throw new BusinessException(
        Messages.MONGO_AGGREGATE_STAGE_SHAPE_INVALID_MSG(
          position,
          describeStage(stage),
        ),
        HttpCode.BAD_REQUEST,
        ErrorIds.PARAM_PARSE_FAILED,
      );
    }

    const keys: string[] = Object.keys(stage);
    const stageName: string = keys[0] ?? "";
    if (
      keys.length !== 1 ||
      !MongoTools.ALLOWED_AGGREGATE_STAGES.has(stageName)
    ) {
      throw new BusinessException(
        Messages.MONGO_AGGREGATE_STAGE_NOT_ALLOWED_MSG(
          position,
          stageName || "unknown",
        ),
        HttpCode.BAD_REQUEST,
        ErrorIds.PARAM_PARSE_FAILED,
      );
    }

    const stageValue: unknown = stage[stageName];
    this.assertStageValue(stageName, stageValue);
    return [stageName, stageValue];
  }

  /**
   * 校验阶段值的基本类型，避免把非法参数透传给 MongoDB 造成难以理解的报错
   */
  private assertStageValue(stageName: string, stageValue: unknown): void {
    const invalid = (): never => {
      throw new BusinessException(
        Messages.MONGO_AGGREGATE_STAGE_VALUE_INVALID_MSG(stageName),
        HttpCode.BAD_REQUEST,
        ErrorIds.PARAM_PARSE_FAILED,
      );
    };

    if (stageName === "$limit") {
      if (typeof stageValue !== "number" || !Number.isFinite(stageValue)) {
        invalid();
      }
      return;
    }

    if (stageName === "$count") {
      if (typeof stageValue !== "string" || !stageValue.trim()) {
        invalid();
      }
      return;
    }

    if (stageName === "$group") {
      if (
        stageValue === null ||
        typeof stageValue !== "object" ||
        Array.isArray(stageValue) ||
        !Object.prototype.hasOwnProperty.call(stageValue, "_id")
      ) {
        invalid();
      }
      return;
    }

    if (stageName === "$unwind") {
      if (typeof stageValue === "string" && stageValue.trim()) {
        return;
      }
      if (
        stageValue !== null &&
        typeof stageValue === "object" &&
        !Array.isArray(stageValue) &&
        typeof (stageValue as Record<string, unknown>).path === "string"
      ) {
        return;
      }
      invalid();
    }

    if (
      stageValue === null ||
      typeof stageValue !== "object" ||
      Array.isArray(stageValue)
    ) {
      invalid();
    }
  }

  /**
   * 把 $limit 阶段的取值收敛到 [1, 上限]
   */
  private resolveStageLimit(stageValue: unknown, safeLimit: number): number {
    const parsed: number = Number(stageValue);
    if (!Number.isFinite(parsed)) {
      throw new BusinessException(
        Messages.MONGO_AGGREGATE_STAGE_VALUE_INVALID_MSG("$limit"),
        HttpCode.BAD_REQUEST,
        ErrorIds.PARAM_PARSE_FAILED,
      );
    }
    return Math.min(Math.max(Math.trunc(parsed), 1), safeLimit);
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
          if (key.startsWith("$") && MongoTools.FORBIDDEN_OPERATORS.has(key)) {
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
 * 把非法阶段序列化成可读片段回显给调用方，便于据此定位与修正参数
 */
function describeStage(stage: unknown): string {
  try {
    const text: string =
      typeof stage === "string" ? stage : JSON.stringify(stage);
    return (text ?? String(stage)).slice(0, 120);
  } catch {
    return String(stage);
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

import { Injectable } from "@nestjs/common";
import { InjectModel } from "@nestjs/mongoose";
import dayjs from "dayjs";
import timezone from "dayjs/plugin/timezone";
import utc from "dayjs/plugin/utc";
import { Model, Types } from "mongoose";
import { Defaults, Messages } from "src/common/constants";
import { LoggerService } from "src/module/common/logger/logger.service";
import { LogDeletion, LogDeletionDocument } from "./schema/logDeletion.schema";

dayjs.extend(utc);
dayjs.extend(timezone);

const TIMEZONE = "Asia/Shanghai";

/**
 * MongoDB 索引信息结构，仅包含索引名
 */
interface MongoIndexInfo {
  name?: string;
}

/**
 * 待记录墓碑的日志来源，按被删日志的主键与原产生时间描述
 */
export interface LogDeletionSource {
  id: string;
  createdAt?: Date;
}

/**
 * 墓碑游标同步返回的单条数据结构，时间为格式化后的字符串
 */
interface LogDeletionSyncItem {
  _id: unknown;
  logType: string;
  eventId: string;
  logCreatedAt?: string;
}

/**
 * 墓碑游标同步的分页结果，含列表与下一页游标
 */
interface LogDeletionSyncPage {
  list: LogDeletionSyncItem[];
  nextCursor: string | null;
}

/**
 * 日志删除墓碑服务，负责记录被删除日志并在数仓同步时按游标下发
 */
@Injectable()
export class LogDeletionService {
  constructor(
    @InjectModel(LogDeletion.name)
    private readonly logDeletionModel: Model<LogDeletionDocument>,
    private readonly logger: LoggerService,
  ) {
    // 索引初始化属于启动期尽力而为的操作，失败只记录日志，不阻塞服务启动
    void this.ensureIndexes().catch((error: unknown) => {
      this.logger.error(
        Messages.LOG_DELETION_INDEX_INIT_FAILED(
          error instanceof Error ? error.message : String(error),
        ),
      );
    });
  }

  /**
   * 确保删除墓碑集合存在幂等唯一索引与 TTL 索引
   */
  private async ensureIndexes(): Promise<void> {
    const collection = this.logDeletionModel.collection;
    const existingIndexes: Record<string, MongoIndexInfo> =
      (await collection.getIndexes()) as Record<string, MongoIndexInfo>;

    const requiredIndexes: Array<{
      spec: Record<string, 1 | -1>;
      options: { name: string; unique?: boolean; expireAfterSeconds?: number };
    }> = [
      {
        spec: { eventId: 1, logType: 1 },
        options: { name: "eventId_1_logType_1", unique: true },
      },
      {
        spec: { createdAt: 1 },
        options: {
          name: "createdAt_ttl",
          expireAfterSeconds: Defaults.LOG_DELETION_TTL_SECONDS,
        },
      },
    ];

    // 检查并创建缺失的索引（并行批量创建，避免启动期串行等待）
    const missingIndexes = requiredIndexes.filter(
      (indexConfig) =>
        !Object.values(existingIndexes).some(
          (index: MongoIndexInfo) => index.name === indexConfig.options.name,
        ),
    );
    if (missingIndexes.length > 0) {
      await Promise.all(
        missingIndexes.map((indexConfig) =>
          collection.createIndex(indexConfig.spec, indexConfig.options),
        ),
      );
      missingIndexes.forEach((indexConfig) => {
        this.logger.info(
          Messages.LOG_DELETION_INDEX_CREATED(indexConfig.options.name),
        );
      });
    }
  }

  /**
   * 记录一批被删除日志的墓碑，必须在真正删除日志之前调用，重复记录按主键幂等忽略
   * @param logType 日志类型标识，取值见 LogTypes
   * @param logs 被删除日志的主键与原产生时间
   */
  async recordDeletions(
    logType: string,
    logs: LogDeletionSource[],
  ): Promise<void> {
    if (logs.length === 0) {
      return;
    }
    const documents = logs.map((log) => ({
      logType,
      eventId: log.id,
      logCreatedAt: log.createdAt ?? new Date(),
    }));
    try {
      await this.logDeletionModel.insertMany(documents, { ordered: false });
    } catch (error: unknown) {
      // 同一日志可能被重复删除，主键冲突属于幂等场景，其余错误必须抛出以免删除无法传播到数仓
      if (!this.isDuplicateKeyError(error)) {
        throw error;
      }
    }
  }

  /**
   * 判断写入失败是否全部由主键冲突引起
   */
  private isDuplicateKeyError(error: unknown): boolean {
    const writeErrors = (error as { writeErrors?: Array<{ code?: number }> })
      .writeErrors;
    if (Array.isArray(writeErrors) && writeErrors.length > 0) {
      return writeErrors.every((item) => item.code === 11000);
    }
    return (error as { code?: number }).code === 11000;
  }

  /**
   * 游标同步删除墓碑（供 FastAPI 数仓按 MongoDB ID 游标拉取并清除 ODS 数据）
   * @param cursor 上一次同步的最后一个 MongoDB ID
   * @param limit 单页数量
   */
  async findByCursor(
    cursor: string | null,
    limit: number,
  ): Promise<LogDeletionSyncPage> {
    const safeLimit: number = Math.min(
      Math.max(limit || 1000, 1),
      Defaults.LOG_DELETION_SYNC_MAX_LIMIT,
    );
    const filter =
      cursor && Types.ObjectId.isValid(cursor)
        ? { _id: { $gt: new Types.ObjectId(cursor) } }
        : {};
    const list: LogDeletionDocument[] = await this.logDeletionModel
      .find(filter)
      .sort({ _id: 1 })
      .limit(safeLimit + 1)
      .lean<LogDeletionDocument[]>()
      .exec();
    const hasMore: boolean = list.length > safeLimit;
    const page: LogDeletionDocument[] = hasMore
      ? list.slice(0, safeLimit)
      : list;
    const lastItem: LogDeletionDocument | undefined = page[page.length - 1];
    return {
      list: page.map(
        (item: LogDeletionDocument): LogDeletionSyncItem => ({
          _id: item._id,
          logType: item.logType,
          eventId: item.eventId,
          logCreatedAt: item.logCreatedAt
            ? dayjs(item.logCreatedAt)
                .tz(TIMEZONE)
                .format("YYYY-MM-DD HH:mm:ss")
            : undefined,
        }),
      ),
      nextCursor: hasMore && lastItem ? String(lastItem._id) : null,
    };
  }
}

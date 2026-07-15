import { Injectable } from "@nestjs/common";
import { InjectModel } from "@nestjs/mongoose";
import dayjs from "dayjs";
import isLeapYear from "dayjs/plugin/isLeapYear";
import timezone from "dayjs/plugin/timezone";
import utc from "dayjs/plugin/utc";
import { Model } from "mongoose";
import { Messages } from "src/common/constants";
import { BusinessException } from "src/common/exceptions/business.exception";
import { logger } from "src/common/utils/writeLog";
import { CreateApiLogDto, QueryApiLogDto } from "./dto/apiLog.dto";
import { ApiLog, ApiLogDocument } from "./schema/apiLog.schema";

dayjs.extend(utc);
dayjs.extend(timezone);
dayjs.extend(isLeapYear);

const TIMEZONE = "Asia/Shanghai";

interface MongoIndexInfo {
  name?: string;
}

interface ApiLogListItem {
  _id: unknown;
  userId: number;
  username: string;
  apiDescription: string;
  apiPath: string;
  apiMethod: string;
  queryParams: Record<string, unknown>;
  pathParams: Record<string, unknown>;
  requestBody: Record<string, unknown>;
  responseTime: number;
  createdAt?: string;
  updatedAt?: string;
}

interface ApiLogPageResult {
  total: number;
  list: ApiLogListItem[];
}

@Injectable()
export class ApiLogService {
  constructor(
    @InjectModel(ApiLog.name)
    private readonly apiLogModel: Model<ApiLogDocument>,
  ) {
    this.ensureIndexes();
  }

  /**
   * 确保数据库中存在必要的索引
   * 如果索引不存在则自动创建
   */
  private async ensureIndexes(): Promise<void> {
    const collection = this.apiLogModel.collection;
    const existingIndexes: Record<string, MongoIndexInfo> =
      (await collection.getIndexes()) as Record<string, MongoIndexInfo>;

    // 定义需要的索引
    const requiredIndexes: Array<{
      spec: Record<string, 1 | -1>;
      options: { name: string };
    }> = [
      {
        spec: { userId: 1, createdAt: -1 },
        options: { name: "userId_1_createdAt_-1" },
      },
      { spec: { createdAt: -1 }, options: { name: "createdAt_-1" } },
      {
        spec: { apiPath: 1, createdAt: -1 },
        options: { name: "apiPath_1_createdAt_-1" },
      },
      {
        spec: { userId: 1, apiMethod: 1, createdAt: -1 },
        options: { name: "userId_1_apiMethod_1_createdAt_-1" },
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
        logger.info(`ApiLog 索引已创建: ${indexConfig.options.name}`);
      });
    }
  }

  /**
   * 创建API日志
   * @param dto 创建日志DTO
   */
  async create(dto: CreateApiLogDto): Promise<void> {
    this.apiLogModel.create(dto);
  }

  /**
   * 根据ID删除日志
   * @param id 日志ID
   */
  async removeById(id: string): Promise<void> {
    const existingLog = await this.apiLogModel.findById(id).exec();
    if (!existingLog) {
      throw BusinessException.notFound(Messages.API_LOG_NOT_FOUND);
    }
    this.apiLogModel.findByIdAndDelete(id).exec();
  }

  /**
   * 批量删除日志
   * @param ids 日志ID数组
   */
  async removeByIds(ids: string[]): Promise<void> {
    // 先检查所有记录是否存在
    const existingLogs = await this.apiLogModel
      .find({ _id: { $in: ids } })
      .exec();
    const existingIds = existingLogs.map((log) => log.id);

    // 找出不存在的ID
    const notFoundIds = ids.filter((id) => !existingIds.includes(id));
    if (notFoundIds.length > 0) {
      throw BusinessException.notFound(Messages.API_LOG_PARTIAL_NOT_FOUND);
    }

    this.apiLogModel.deleteMany({ _id: { $in: ids } }).exec();
  }

  /**
   * 根据条件查询日志（分页）
   * @param query 查询条件
   */
  async findByFilter(query: QueryApiLogDto): Promise<ApiLogPageResult> {
    const {
      userId,
      username,
      apiDescription,
      apiPath,
      apiMethod,
      startTime,
      endTime,
      page = "1",
      size = "10",
    } = query;

    const filters: Record<string, unknown> = {};

    if (userId) filters.userId = Number(userId);
    if (username) filters.username = { $regex: username, $options: "i" };
    if (apiDescription)
      filters.apiDescription = { $regex: apiDescription, $options: "i" };
    if (apiPath) filters.apiPath = { $regex: apiPath, $options: "i" };
    if (apiMethod) filters.apiMethod = apiMethod;

    if (startTime || endTime) {
      const createdAtFilter: Record<string, Date> = {};
      if (startTime)
        createdAtFilter.$gte = dayjs(startTime, "YYYY-MM-DD HH:mm:ss").toDate();
      if (endTime)
        createdAtFilter.$lte = dayjs(endTime, "YYYY-MM-DD HH:mm:ss").toDate();
      filters.createdAt = createdAtFilter;
    }

    const skip: number = (parseInt(page) - 1) * parseInt(size);
    const take: number = parseInt(size);

    const [total, list] = await Promise.all([
      this.apiLogModel.countDocuments(filters),
      this.apiLogModel
        .find(filters)
        .sort({ createdAt: -1 })
        .skip(skip)
        .limit(take)
        .exec(),
    ]);

    // 格式化返回数据
    const resultList: ApiLogListItem[] = list.map((log: ApiLogDocument) => ({
      _id: log._id,
      userId: log.userId,
      username: log.username,
      apiDescription: log.apiDescription,
      apiPath: log.apiPath,
      apiMethod: log.apiMethod,
      queryParams: log.queryParams,
      pathParams: log.pathParams,
      requestBody: log.requestBody,
      responseTime: log.responseTime,
      createdAt: log.createdAt
        ? dayjs(log.createdAt).tz(TIMEZONE).format("YYYY-MM-DD HH:mm:ss")
        : undefined,
      updatedAt: log.updatedAt
        ? dayjs(log.updatedAt).tz(TIMEZONE).format("YYYY-MM-DD HH:mm:ss")
        : undefined,
    }));

    return { total, list: resultList };
  }

  /**
   * 删除指定日期之前的过期日志
   * 供 TaskModule 定时任务调用，避免 common 层直接操作 system 层 schema
   * @param before 删除此日期之前的日志
   * @returns 删除的日志数量
   */
  async cleanupOldLogs(before: Date): Promise<number> {
    const result = await this.apiLogModel
      .deleteMany({ createdAt: { $lt: before } })
      .exec();
    return result.deletedCount;
  }
}

import { Injectable } from "@nestjs/common";
import { InjectModel } from "@nestjs/mongoose";
import dayjs from "dayjs";
import isLeapYear from "dayjs/plugin/isLeapYear";
import timezone from "dayjs/plugin/timezone";
import utc from "dayjs/plugin/utc";
import { DeleteResult, Model } from "mongoose";
import { Messages } from "src/common/constants";
import { BusinessException } from "src/common/exceptions/business.exception";
import { logger } from "src/common/utils/writeLog";
import { ArticleService } from "src/module/system/article/article.service";
import { UserService } from "src/module/system/user/user.service";
import { CreateArticleLogDto, QueryArticleLogDto } from "./dto/articleLog.dto";
import { ArticleLog, ArticleLogDocument } from "./schema/articleLog.schema";

dayjs.extend(utc);
dayjs.extend(timezone);
dayjs.extend(isLeapYear);

const TIMEZONE = "Asia/Shanghai";

interface MongoIndexInfo {
  name?: string;
}

interface ArticleLogListItem {
  _id: unknown;
  userId: number;
  username: string;
  articleId: number;
  articleTitle: string;
  action: string;
  content: Record<string, unknown>;
  msg?: string;
  createdAt?: string;
  updatedAt?: string;
}

interface ArticleLogPageResult {
  total: number;
  list: ArticleLogListItem[];
}

@Injectable()
export class ArticleLogService {
  constructor(
    @InjectModel(ArticleLog.name)
    private readonly logModel: Model<ArticleLogDocument>,
    private readonly userService: UserService,
    private readonly articleService: ArticleService,
  ) {
    this.ensureIndexes();
  }

  /**
   * 确保数据库中存在必要的索引
   * 如果索引不存在则自动创建
   */
  private async ensureIndexes(): Promise<void> {
    const collection = this.logModel.collection;
    const existingIndexes: Record<string, MongoIndexInfo> =
      (await collection.getIndexes()) as Record<string, MongoIndexInfo>;

    // 定义需要的索引
    const requiredIndexes: Array<{
      spec: Record<string, 1 | -1>;
      options: { name: string };
    }> = [
      { spec: { createdAt: -1 }, options: { name: "createdAt_-1" } },
      {
        spec: { userId: 1, createdAt: -1 },
        options: { name: "userId_1_createdAt_-1" },
      },
      {
        spec: { articleId: 1, createdAt: -1 },
        options: { name: "articleId_1_createdAt_-1" },
      },
      {
        spec: { action: 1, createdAt: -1 },
        options: { name: "action_1_createdAt_-1" },
      },
      {
        spec: { userId: 1, action: 1, articleId: 1 },
        options: { name: "userId_1_action_1_articleId_1" },
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
        logger.info(
          Messages.ARTICLE_LOG_INDEX_CREATED(indexConfig.options.name),
        );
      });
    }
  }

  async create(dto: CreateArticleLogDto): Promise<void> {
    this.logModel.create(dto);
  }

  async removeById(id: string): Promise<ArticleLogDocument | null> {
    const existingLog: ArticleLogDocument | null = await this.logModel
      .findById(id)
      .exec();
    if (!existingLog) {
      throw BusinessException.notFound(Messages.ARTICLE_LOG_NOT_FOUND);
    }
    return this.logModel.findByIdAndDelete(id).exec();
  }

  async removeByIds(ids: string[]): Promise<DeleteResult> {
    // 先检查所有记录是否存在
    const existingLogs: ArticleLogDocument[] = await this.logModel
      .find({ _id: { $in: ids } })
      .exec();
    const existingIds: string[] = existingLogs.map(
      (log: ArticleLogDocument) => log.id,
    );

    // 找出不存在的ID
    const notFoundIds: string[] = ids.filter(
      (id: string) => !existingIds.includes(id),
    );
    if (notFoundIds.length > 0) {
      throw BusinessException.notFound(Messages.ARTICLE_LOG_PARTIAL_NOT_FOUND);
    }

    return this.logModel.deleteMany({ _id: { $in: ids } }).exec();
  }

  async findByFilter(query: QueryArticleLogDto): Promise<ArticleLogPageResult> {
    const {
      userId,
      articleId,
      username,
      articleTitle,
      action,
      startTime,
      endTime,
      page = "1",
      size = "10",
    } = query;

    const filters: Record<string, unknown> = {};
    if (userId) filters.userId = Number(userId);
    if (articleId) filters.articleId = Number(articleId);
    if (action) filters.action = action;

    // 根据用户名和文章标题并行查找匹配的用户ID和文章ID（两次查询独立，Promise.all 降低延迟）
    if (username || articleTitle) {
      const [users, articles] = await Promise.all([
        username
          ? this.userService.getUsersByName(username)
          : Promise.resolve([]),
        articleTitle
          ? this.articleService.getArticlesByTitle(articleTitle)
          : Promise.resolve([]),
      ]);

      if (username) {
        const userIds = users.map((user) => user.id);
        if (userIds.length === 0) {
          return { total: 0, list: [] };
        }
        filters.userId = { $in: userIds };
      }

      if (articleTitle) {
        const articleIds = articles.map((article) => article.id);
        if (articleIds.length === 0) {
          return { total: 0, list: [] };
        }
        filters.articleId = { $in: articleIds };
      }
    }

    if (startTime || endTime) {
      const createdAtFilter: Record<string, Date> = {};
      if (startTime)
        createdAtFilter.$gte = dayjs(startTime, "YYYY-MM-DD HH:mm:ss").toDate();
      if (endTime)
        createdAtFilter.$lte = dayjs(endTime, "YYYY-MM-DD HH:mm:ss").toDate();
      filters.createdAt = createdAtFilter;
    }

    const pageNum: number = parseInt(page);
    const take: number = parseInt(size);

    const [total, list] = await Promise.all([
      this.logModel.countDocuments(filters),
      // 优化大分页查询：当page > 100时，使用hint强制使用索引避免扫描全表
      pageNum > 100
        ? this.logModel
            .find(filters)
            .sort({ createdAt: -1 })
            .hint({ createdAt: -1 })
            .skip((pageNum - 1) * take)
            .limit(take)
            .exec()
        : this.logModel
            .find(filters)
            .sort({ createdAt: -1 })
            .skip((pageNum - 1) * take)
            .limit(take)
            .exec(),
    ]);
    // 收集所有不重复的 userId 和 articleId，批量查询（消除 N+1）
    const userIds: number[] = [
      ...new Set(list.map((log: ArticleLogDocument) => log.userId)),
    ];
    const articleIds: number[] = [
      ...new Set(list.map((log: ArticleLogDocument) => log.articleId)),
    ];

    const [users, articles] = await Promise.all([
      userIds.length > 0
        ? this.userService.getUserByIds(userIds)
        : Promise.resolve([]),
      articleIds.length > 0
        ? this.articleService.getArticleByIds(articleIds)
        : Promise.resolve([]),
    ]);

    // 构建 userId → username 和 articleId → title 的映射表
    const userMap: Map<number, string> = new Map(
      users.map((user) => [user.id, user.name]),
    );
    const articleMap: Map<number, string> = new Map(
      articles.map((article) => [article.id, article.title]),
    );

    // 组装结果列表（内存映射，不再逐条查库）
    const resultList: ArticleLogListItem[] = list.map(
      (log: ArticleLogDocument): ArticleLogListItem => ({
        _id: log._id,
        userId: log.userId,
        username: userMap.get(log.userId) || "",
        articleId: log.articleId,
        articleTitle: articleMap.get(log.articleId) || "",
        action: log.action,
        content: log.content,
        msg: log.msg,
        createdAt: log.createdAt
          ? dayjs(log.createdAt).tz(TIMEZONE).format("YYYY-MM-DD HH:mm:ss")
          : undefined,
        updatedAt: log.updatedAt
          ? dayjs(log.updatedAt).tz(TIMEZONE).format("YYYY-MM-DD HH:mm:ss")
          : undefined,
      }),
    );
    return { total, list: resultList };
  }

  /**
   * 删除指定日期之前的过期日志
   * 供 TaskModule 定时任务调用，避免 common 层直接操作 system 层 schema
   * @param before 删除此日期之前的日志
   * @returns 删除的日志数量
   */
  async cleanupOldLogs(before: Date): Promise<number> {
    const result = await this.logModel
      .deleteMany({ createdAt: { $lt: before } })
      .exec();
    return result.deletedCount;
  }
}

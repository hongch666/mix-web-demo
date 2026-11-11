import { Injectable } from "@nestjs/common";
import { InjectModel } from "@nestjs/mongoose";
import dayjs from "dayjs";
import isLeapYear from "dayjs/plugin/isLeapYear";
import timezone from "dayjs/plugin/timezone";
import utc from "dayjs/plugin/utc";
import { DeleteResult, Model, Types } from "mongoose";
import { Defaults, Messages, RedisKeys } from "src/common/constants";
import { BusinessException } from "src/common/exceptions/business.exception";
import type { CreatedAtCursor } from "src/common/utils/createdAtCursor.util";
import {
  CREATED_AT_CURSOR_INDEX,
  CREATED_AT_DESC_SORT,
  buildCreatedAtSeekFilter,
  encodeCreatedAtCursor,
  parseCreatedAtCursor,
} from "src/common/utils/createdAtCursor.util";
import { Cacheable } from "src/framework/decorators/cache.decorator";
import { LoggerService } from "src/module/common/logger/logger.service";
import { SpringClientService } from "src/module/common/client/springClient.service";
import {
  ArticleAction,
  CreateArticleLogDto,
  QueryArticleLogDto,
} from "./dto/articleLog.dto";
import { ArticleLog, ArticleLogDocument } from "./schema/articleLog.schema";

dayjs.extend(utc);
dayjs.extend(timezone);
dayjs.extend(isLeapYear);

const TIMEZONE = "Asia/Shanghai";

/**
 * MongoDB 索引信息结构，仅包含索引名
 */
interface MongoIndexInfo {
  name?: string;
}

/**
 * 文章日志分页列表项数据结构，含远程映射的用户名与文章标题
 */
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

/**
 * 文章日志分页查询结果，含总数、列表与下一页游标
 */
interface ArticleLogPageResult {
  total: number;
  list: ArticleLogListItem[];
  nextCursor: string | null;
}

/** lean 查询返回的纯对象结构，_id 直接透传给前端 */
type LeanArticleLog = ArticleLog & { _id: Types.ObjectId };

/**
 * 文章日志游标同步返回的单条数据结构
 */
interface ArticleLogSyncItem {
  _id: unknown;
  userId: number;
  articleId: number;
  action: string;
  content: Record<string, unknown>;
  createdAt?: Date;
}

/**
 * 文章日志服务，负责日志写入、条件分页查询、删除及搜索关键词与浏览分布的聚合统计
 */
@Injectable()
export class ArticleLogService {
  constructor(
    @InjectModel(ArticleLog.name)
    private readonly logModel: Model<ArticleLogDocument>,
    private readonly springClient: SpringClientService,
    private readonly logger: LoggerService,
  ) {
    // 索引初始化属于启动期尽力而为的操作，失败只记录日志，不阻塞服务启动
    void this.ensureIndexes().catch((error: unknown) => {
      this.logger.error(
        Messages.ARTICLE_LOG_INDEX_INIT_FAILED(
          error instanceof Error ? error.message : String(error),
        ),
      );
    });
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
        spec: { userId: 1, action: 1, createdAt: -1 },
        options: { name: "userId_1_action_1_createdAt_-1" },
      },
      {
        spec: { userId: 1, articleId: 1, createdAt: -1 },
        options: { name: "userId_1_articleId_1_createdAt_-1" },
      },
      {
        spec: { createdAt: -1, _id: -1 },
        options: { name: CREATED_AT_CURSOR_INDEX },
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
          Messages.ARTICLE_LOG_INDEX_CREATED(indexConfig.options.name),
        );
      });
    }
  }

  /**
   * 批量创建文章操作日志（攒批写入）
   * 使用 ordered:false 让单条错误文档不影响整批写入
   * @param dtos 日志DTO数组
   */
  async insertMany(dtos: CreateArticleLogDto[]): Promise<void> {
    if (dtos.length === 0) return;
    await this.logModel.insertMany(dtos, { ordered: false });
  }

  /**
   * 根据 ID 删除文章日志，日志不存在时抛出业务异常
   */
  async removeById(id: string): Promise<ArticleLogDocument | null> {
    const existingLog: ArticleLogDocument | null = await this.logModel
      .findById(id)
      .exec();
    if (!existingLog) {
      throw BusinessException.notFound(Messages.ARTICLE_LOG_NOT_FOUND);
    }
    return this.logModel.findByIdAndDelete(id).exec();
  }

  /**
   * 批量删除文章日志，任一 ID 不存在时抛出业务异常
   */
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

  /**
   * 按条件分页查询文章日志，用户名与文章标题先经 Spring 服务解析为对应 ID，并批量映射用户名和标题消除 N+1 查询
   */
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

    // 根据用户名和文章标题并行查找匹配的用户ID和文章ID
    if (username || articleTitle) {
      const [userResult, articleResult] = await Promise.all([
        username
          ? this.springClient.getUsersByName(username)
          : Promise.resolve(null),
        articleTitle
          ? this.springClient.getArticlesByTitle(articleTitle)
          : Promise.resolve(null),
      ]);

      const users: Array<{ id: number }> = userResult
        ? (SpringClientService.extractData<Array<{ id: number }>>(userResult) ??
          [])
        : [];
      const articles: Array<{ id: number }> = articleResult
        ? (SpringClientService.extractData<Array<{ id: number }>>(
            articleResult,
          ) ?? [])
        : [];

      if (username) {
        const userIds = users.map((user) => user.id);
        if (userIds.length === 0) {
          return { total: 0, list: [], nextCursor: null };
        }
        filters.userId = { $in: userIds };
      }

      if (articleTitle) {
        const articleIds = articles.map((article) => article.id);
        if (articleIds.length === 0) {
          return { total: 0, list: [], nextCursor: null };
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

    const take: number = parseInt(size);
    const cursor: CreatedAtCursor | null = parseCreatedAtCursor(query.cursor);
    // 带游标时按 createdAt + _id 做 seek 翻页，只有首页或未带游标才退回 skip
    const pageFilters: Record<string, unknown> = cursor
      ? { ...filters, ...buildCreatedAtSeekFilter(cursor) }
      : filters;
    const skip: number = cursor ? 0 : (parseInt(page) - 1) * take;
    const hasFilter: boolean = Object.keys(filters).length > 0;

    // 首页与游标翻页本身没有 skip 成本走单阶段查询，跳页才用两阶段减少 skip 阶段的文档回表
    const listTask: Promise<LeanArticleLog[]> =
      skip > 0
        ? this.findPageBySkip(
            pageFilters,
            skip,
            take,
            hasFilter ? undefined : CREATED_AT_CURSOR_INDEX,
          )
        : this.logModel
            .find(pageFilters)
            .sort(CREATED_AT_DESC_SORT)
            .limit(take)
            .lean<LeanArticleLog[]>()
            .exec();

    // 无过滤条件时用 estimatedDocumentCount 读集合元数据，避免全集合计数随日志量线性变慢
    const countTask: Promise<number> = hasFilter
      ? this.logModel.countDocuments(filters).exec()
      : this.logModel.estimatedDocumentCount().exec();

    const [total, list] = await Promise.all([countTask, listTask]);

    const lastLog: LeanArticleLog | undefined = list[list.length - 1];
    const nextCursor: string | null =
      list.length === take && lastLog?.createdAt
        ? encodeCreatedAtCursor(lastLog.createdAt, lastLog._id)
        : null;

    // 收集所有不重复的 userId 和 articleId，按批解析显示名以消除 N+1
    const userIds: number[] = [
      ...new Set(list.map((log: LeanArticleLog) => log.userId)),
    ];
    const articleIds: number[] = [
      ...new Set(list.map((log: LeanArticleLog) => log.articleId)),
    ];

    const [userMap, articleMap]: [
      Record<number, string>,
      Record<number, string>,
    ] = await Promise.all([
      userIds.length > 0
        ? this.loadUserNameMap(userIds)
        : Promise.resolve<Record<number, string>>({}),
      articleIds.length > 0
        ? this.loadArticleTitleMap(articleIds)
        : Promise.resolve<Record<number, string>>({}),
    ]);

    // 组装结果列表（内存映射，不再逐条查库）
    const resultList: ArticleLogListItem[] = list.map(
      (log: LeanArticleLog): ArticleLogListItem => ({
        _id: log._id,
        userId: log.userId,
        username: userMap[log.userId] ?? "",
        articleId: log.articleId,
        articleTitle: articleMap[log.articleId] ?? "",
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
    return { total, list: resultList, nextCursor };
  }

  /**
   * 跳页的两阶段查询，第一阶段只按索引取一页 _id，第二阶段按 _id 回表，让 skip 丢弃的记录不产生文档读取
   * @param filters 查询条件，必须与首页请求保持一致
   * @param skip 跳过的条数
   * @param take 每页条数
   * @param hint 无过滤条件时强制使用覆盖索引，避免优化器改选其他索引
   */
  private async findPageBySkip(
    filters: Record<string, unknown>,
    skip: number,
    take: number,
    hint?: string,
  ): Promise<LeanArticleLog[]> {
    const idQuery = this.logModel
      .find(filters, { _id: 1 })
      .sort(CREATED_AT_DESC_SORT)
      .skip(skip)
      .limit(take)
      .lean<Array<{ _id: Types.ObjectId }>>();
    if (hint) {
      idQuery.hint(hint);
    }

    const idDocs: Array<{ _id: Types.ObjectId }> = await idQuery.exec();
    const ids: Types.ObjectId[] = idDocs.map((doc) => doc._id);
    if (ids.length === 0) {
      return [];
    }

    // 回表不保证返回顺序，按第一阶段取到的 _id 顺序还原
    const docs: LeanArticleLog[] = await this.logModel
      .find({ _id: { $in: ids } })
      .lean<LeanArticleLog[]>()
      .exec();
    const byId: Map<string, LeanArticleLog> = new Map(
      docs.map((doc): [string, LeanArticleLog] => [String(doc._id), doc]),
    );
    return ids
      .map((id) => byId.get(String(id)))
      .filter((doc): doc is LeanArticleLog => doc !== undefined);
  }

  /**
   * 批量解析用户 ID 到用户名的映射
   * L1 10 秒只服务单实例内的并发翻页，L2 5 分钟覆盖多实例与连续刷新，过期后自然回源
   */
  @Cacheable<[number[]]>({
    key: (userIds: number[]): string =>
      RedisKeys.CACHE_ARTICLE_LOG_USER_NAMES(userIds),
    localTtl: Defaults.ARTICLE_LOG_MAPPING_LOCAL_TTL_SECONDS,
    redisTtl: Defaults.ARTICLE_LOG_MAPPING_REDIS_TTL_SECONDS,
  })
  async loadUserNameMap(userIds: number[]): Promise<Record<number, string>> {
    const result: Record<string, unknown> =
      await this.springClient.getUserByIds(userIds);
    const users: Array<{ id: number; name: string }> =
      SpringClientService.extractData<Array<{ id: number; name: string }>>(
        result,
      ) ?? [];
    return users.reduce<Record<number, string>>((acc, user) => {
      acc[user.id] = user.name;
      return acc;
    }, {});
  }

  /**
   * 批量解析文章 ID 到标题的映射，缓存策略与用户名映射保持一致
   */
  @Cacheable<[number[]]>({
    key: (articleIds: number[]): string =>
      RedisKeys.CACHE_ARTICLE_LOG_ARTICLE_TITLES(articleIds),
    localTtl: Defaults.ARTICLE_LOG_MAPPING_LOCAL_TTL_SECONDS,
    redisTtl: Defaults.ARTICLE_LOG_MAPPING_REDIS_TTL_SECONDS,
  })
  async loadArticleTitleMap(
    articleIds: number[],
  ): Promise<Record<number, string>> {
    const result: Record<string, unknown> =
      await this.springClient.getArticleByIds(articleIds);
    const articles: Array<{ id: number; title: string }> =
      SpringClientService.extractData<Array<{ id: number; title: string }>>(
        result,
      ) ?? [];
    return articles.reduce<Record<number, string>>((acc, article) => {
      acc[article.id] = article.title;
      return acc;
    }, {});
  }

  /**
   * 按 MongoDB ID 游标增量拉取文章日志并返回下一页游标，供数仓同步
   */
  async findByCursor(
    cursor: string | null,
    limit: number,
  ): Promise<{ list: ArticleLogSyncItem[]; nextCursor: string | null }> {
    const safeLimit: number = Math.min(Math.max(limit || 1000, 1), 5000);
    const filter =
      cursor && Types.ObjectId.isValid(cursor)
        ? { _id: { $gt: new Types.ObjectId(cursor) } }
        : {};
    const list: ArticleLogDocument[] = await this.logModel
      .find(filter)
      .sort({ _id: 1 })
      .limit(safeLimit + 1)
      .lean<ArticleLogDocument[]>()
      .exec();
    const hasMore: boolean = list.length > safeLimit;
    const page: ArticleLogDocument[] = hasMore
      ? list.slice(0, safeLimit)
      : list;
    const lastItem: ArticleLogDocument | undefined = page[page.length - 1];
    return {
      list: page.map(
        (item: ArticleLogDocument): ArticleLogSyncItem => ({
          _id: item._id,
          userId: item.userId,
          articleId: item.articleId,
          action: item.action,
          content: item.content,
          createdAt: item.createdAt,
        }),
      ),
      nextCursor: hasMore && lastItem ? String(lastItem._id) : null,
    };
  }

  /**
   * 获取用户搜索历史关键词（供 GoZero 内部远程调用）
   * 从 articlelogs 集合中聚合出指定用户最近去重后的搜索关键词，最多 10 条
   * @param userId 用户ID
   * @returns 搜索关键词列表（按时间倒序，去重）
   */
  async getSearchHistory(userId: number): Promise<string[]> {
    const result = await this.logModel
      .aggregate([
        { $match: { userId, action: ArticleAction.SEARCH } },
        { $sort: { createdAt: -1 } },
        { $addFields: { keyword: "$content.Keyword" } },
        { $match: { keyword: { $exists: true, $nin: [null, ""] } } },
        { $group: { _id: "$keyword", createdAt: { $first: "$createdAt" } } },
        { $sort: { createdAt: -1 } },
        { $limit: 10 },
        { $project: { _id: 0, keyword: "$_id" } },
      ])
      .exec();

    return result.map((item) => item.keyword as string);
  }

  /**
   * 获取用户文章浏览分布（供 FastAPI 内部远程调用）
   * 从 articlelogs 集合聚合出指定用户浏览过的文章及浏览次数，按浏览次数倒序
   * @param userId 用户ID
   */
  async getViewDistribution(userId: number): Promise<{
    total_views: number;
    articles: Array<{ article_id: number; title: string; views: number }>;
  }> {
    const results = await this.logModel
      .aggregate([
        { $match: { userId, action: ArticleAction.VIEW } },
        { $group: { _id: "$articleId", views: { $sum: 1 } } },
        { $match: { _id: { $ne: null } } },
        { $sort: { views: -1 } },
      ])
      .exec();

    if (results.length === 0) {
      return { total_views: 0, articles: [] };
    }

    const articleIds: number[] = results.map((doc) => doc._id as number);
    const articleResult = await this.springClient.getArticleByIds(articleIds);
    const articles: Array<{ id: number; title: string }> =
      SpringClientService.extractData<Array<{ id: number; title: string }>>(
        articleResult,
      ) ?? [];
    const articleMap: Map<number, string> = new Map(
      articles.map((article) => [article.id, article.title]),
    );

    let totalViews = 0;
    const list = results.map((doc) => {
      const views = doc.views as number;
      totalViews += views;
      return {
        article_id: doc._id as number,
        title: articleMap.get(doc._id as number) || Messages.UNKNOWN_ARTICLE,
        views,
      };
    });

    return { total_views: totalViews, articles: list };
  }

  /**
   * 获取所有搜索关键词（供 FastAPI 词云功能内部远程调用）
   * 从 articlelogs 集合中提取所有 action=search 的去重关键词
   */
  async getSearchKeywords(): Promise<string[]> {
    const results = await this.logModel
      .aggregate([
        { $match: { action: ArticleAction.SEARCH } },
        { $project: { keyword: "$content.Keyword" } },
        { $match: { keyword: { $ne: "", $exists: true } } },
        { $group: { _id: "$keyword" } },
        { $sort: { _id: 1 } },
      ])
      .exec();

    return results.map((doc) => doc._id as string);
  }
}

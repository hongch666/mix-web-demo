import { Injectable } from '@nestjs/common';
import { InjectModel } from '@nestjs/mongoose';
import dayjs from 'dayjs';
import isLeapYear from 'dayjs/plugin/isLeapYear';
import timezone from 'dayjs/plugin/timezone';
import utc from 'dayjs/plugin/utc';
import { DeleteResult, Model } from 'mongoose';
import { BusinessException } from 'src/common/exceptions/business.exception';
import { Constants } from 'src/common/utils/constants';
import { logger } from 'src/common/utils/writeLog';
import {
  ArticleService,
  RemoteArticle,
} from 'src/modules/article/article.service';
import { RemoteUser, UserService } from '../../modules/user/user.service';
import { CreateArticleLogDto, QueryArticleLogDto } from './dto/articleLog.dto';
import { ArticleLog, ArticleLogDocument } from './schema/articleLog.schema';

dayjs.extend(utc);
dayjs.extend(timezone);
dayjs.extend(isLeapYear);

const TIMEZONE = 'Asia/Shanghai';

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
      { spec: { createdAt: -1 }, options: { name: 'createdAt_-1' } },
      {
        spec: { userId: 1, createdAt: -1 },
        options: { name: 'userId_1_createdAt_-1' },
      },
      {
        spec: { articleId: 1, createdAt: -1 },
        options: { name: 'articleId_1_createdAt_-1' },
      },
      {
        spec: { action: 1, createdAt: -1 },
        options: { name: 'action_1_createdAt_-1' },
      },
      {
        spec: { userId: 1, action: 1, articleId: 1 },
        options: { name: 'userId_1_action_1_articleId_1' },
      },
    ];

    // 检查并创建缺失的索引
    for (const indexConfig of requiredIndexes) {
      const indexExists: boolean = Object.values(existingIndexes).some(
        (index: MongoIndexInfo) => index.name === indexConfig.options.name,
      );

      if (!indexExists) {
        await collection.createIndex(indexConfig.spec, indexConfig.options);
        logger.info(`索引已创建: ${indexConfig.options.name}`);
      }
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
      throw BusinessException.notFound(Constants.ARTICLE_LOG_NOT_FOUND);
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
      throw BusinessException.notFound(Constants.ARTICLE_LOG_PARTIAL_NOT_FOUND);
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
      page = '1',
      size = '10',
    } = query;

    const filters: Record<string, unknown> = {};
    if (userId) filters.userId = Number(userId);
    if (articleId) filters.articleId = Number(articleId);
    if (action) filters.action = action;

    // 根据用户名搜索，先查找匹配的用户ID
    if (username) {
      const users = await this.userService.getUsersByName(username);
      const userIds = users.map((user) => user.id);
      if (userIds.length > 0) {
        filters.userId = { $in: userIds };
      } else {
        // 如果没有找到匹配的用户，返回空结果
        return { total: 0, list: [] };
      }
    }

    // 根据文章标题搜索，先查找匹配的文章ID
    if (articleTitle) {
      const articles =
        await this.articleService.getArticlesByTitle(articleTitle);
      const articleIds = articles.map((article) => article.id);
      if (articleIds.length > 0) {
        filters.articleId = { $in: articleIds };
      } else {
        // 如果没有找到匹配的文章，返回空结果
        return { total: 0, list: [] };
      }
    }

    if (startTime || endTime) {
      const createdAtFilter: Record<string, Date> = {};
      if (startTime)
        createdAtFilter.$gte = dayjs(startTime, 'YYYY-MM-DD HH:mm:ss').toDate();
      if (endTime)
        createdAtFilter.$lte = dayjs(endTime, 'YYYY-MM-DD HH:mm:ss').toDate();
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
    const userIds = list.map((log: ArticleLogDocument) => Number(log.userId));
    const articleIds = list.map((log: ArticleLogDocument) =>
      Number(log.articleId),
    );
    const [userMap, articleMap] = await Promise.all([
      this.userService.getUsersByIds(userIds),
      this.articleService.getArticlesByIds(articleIds),
    ]);

    // 只返回指定字段，历史日志关联数据不存在时做降级展示
    const resultList: ArticleLogListItem[] = list.map(
      (log: ArticleLogDocument): ArticleLogListItem => {
        const user: RemoteUser | undefined = userMap.get(Number(log.userId));
        const article: RemoteArticle | undefined = articleMap.get(
          Number(log.articleId),
        );
        return {
          _id: log._id,
          userId: log.userId,
          username: user?.name || Constants.UNKNOWN_USER,
          articleId: log.articleId,
          articleTitle: article?.title || Constants.UNKNOWN_ARTICLE,
          action: log.action,
          content: log.content,
          msg: log.msg,
          createdAt: log.createdAt
            ? dayjs(log.createdAt).tz(TIMEZONE).format('YYYY-MM-DD HH:mm:ss')
            : undefined,
          updatedAt: log.updatedAt
            ? dayjs(log.updatedAt).tz(TIMEZONE).format('YYYY-MM-DD HH:mm:ss')
            : undefined,
        };
      },
    );
    return { total, list: resultList };
  }

  async getSearchHistory(userId: number): Promise<{ keywords: string[] }> {
    const rows: Array<{ keyword?: string }> = await this.logModel.aggregate([
      {
        $match: {
          userId,
          action: 'search',
        },
      },
      {
        $sort: {
          createdAt: -1,
        },
      },
      {
        $addFields: {
          keyword: '$content.Keyword',
        },
      },
      {
        $match: {
          keyword: {
            $exists: true,
            $nin: [null, ''],
          },
        },
      },
      {
        $group: {
          _id: '$keyword',
          createdAt: { $first: '$createdAt' },
        },
      },
      {
        $sort: {
          createdAt: -1,
        },
      },
      {
        $limit: 10,
      },
      {
        $project: {
          _id: 0,
          keyword: '$_id',
        },
      },
    ]);
    return {
      keywords: rows.map((item) => item.keyword).filter(Boolean) as string[],
    };
  }

  async getSearchKeywords(): Promise<{ keywords: string[] }> {
    const rows: Array<{ keyword?: string }> = await this.logModel.aggregate([
      { $match: { action: 'search' } },
      { $project: { keyword: '$content.Keyword' } },
      { $match: { keyword: { $ne: '', $exists: true } } },
      { $group: { _id: '$keyword' } },
      { $sort: { _id: 1 } },
      { $project: { _id: 0, keyword: '$_id' } },
    ]);
    return {
      keywords: rows.map((item) => item.keyword).filter(Boolean) as string[],
    };
  }

  async getViewDistribution(userId: number): Promise<Record<string, unknown>> {
    const rows: Array<{ articleId?: number; views?: number }> =
      await this.logModel.aggregate([
        { $match: { userId, action: 'view' } },
        { $group: { _id: '$articleId', views: { $sum: 1 } } },
        { $match: { _id: { $ne: null } } },
        { $sort: { views: -1 } },
        { $project: { _id: 0, articleId: '$_id', views: 1 } },
      ]);
    return {
      total_views: rows.reduce(
        (total, item) => total + Number(item.views || 0),
        0,
      ),
      articles: rows,
    };
  }
}

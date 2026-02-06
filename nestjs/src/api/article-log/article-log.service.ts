import { Injectable } from '@nestjs/common';
import { InjectModel } from '@nestjs/mongoose';
import { Model, DeleteResult } from 'mongoose';
import { ArticleLog, ArticleLogDocument } from './schema/article-log.schema';
import { CreateArticleLogDto, QueryArticleLogDto } from './dto/article-log.dto';
import { UserService } from '../../modules/user/user.service';
import dayjs from 'dayjs';
import utc from 'dayjs/plugin/utc';
import timezone from 'dayjs/plugin/timezone';
import isLeapYear from 'dayjs/plugin/isLeapYear';
import { ArticleService } from 'src/modules/article/article.service';
import { logger } from 'src/common/utils/writeLog';
import { BusinessException } from 'src/common/exceptions/business.exception';
import { Constants } from 'src/common/utils/constants';

dayjs.extend(utc);
dayjs.extend(timezone);
dayjs.extend(isLeapYear);

const TIMEZONE = 'Asia/Shanghai';

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
    const collection: any = this.logModel.collection;
    const existingIndexes: any = await collection.getIndexes();

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
    ];

    // 检查并创建缺失的索引
    for (const indexConfig of requiredIndexes) {
      const indexExists: boolean = Object.values(existingIndexes).some(
        (index: any) => index.name === indexConfig.options.name,
      );

      if (!indexExists) {
        await collection.createIndex(indexConfig.spec, indexConfig.options);
        logger.info(`索引已创建: ${indexConfig.options.name}`);
      }
    }
  }

  async create(dto: CreateArticleLogDto) {
    // 指定 createdAt 为东八区时间
    return this.logModel.create(dto);
  }

  async removeById(id: string) {
    const existingLog = await this.logModel.findById(id).exec();
    if (!existingLog) {
      throw new BusinessException(Constants.ARTICLE_LOG_NOT_FOUND);
    }
    return this.logModel.findByIdAndDelete(id).exec();
  }

  async removeByIds(ids: string[]): Promise<DeleteResult> {
    // 先检查所有记录是否存在
    const existingLogs: any[] = await this.logModel.find({ _id: { $in: ids } }).exec();
    const existingIds: string[] = existingLogs.map((log: any) => log.id);

    // 找出不存在的ID
    const notFoundIds: string[] = ids.filter((id: string) => !existingIds.includes(id));
    if (notFoundIds.length > 0) {
      throw new BusinessException(Constants.ARTICLE_LOG_PARTIAL_NOT_FOUND);
    }

    return this.logModel.deleteMany({ _id: { $in: ids } }).exec();
  }

  async findByFilter(query: QueryArticleLogDto) {
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

    const filters: Record<string, any> = {};
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
      filters.createdAt = {};
      if (startTime)
        filters.createdAt.$gte = dayjs(
          startTime,
          'YYYY-MM-DD HH:mm:ss',
        ).toDate();
      if (endTime)
        filters.createdAt.$lte = dayjs(endTime, 'YYYY-MM-DD HH:mm:ss').toDate();
    }

    const pageNum = parseInt(page);
    const take = parseInt(size);

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
    // 只返回指定字段
    const resultList = await Promise.all(
      list.map(async (log) => ({
        _id: log._id,
        userId: log.userId,
        username: (await this.userService.getUserById(log.userId))?.name || '',
        articleId: log.articleId,
        articleTitle:
          (await this.articleService.getArticleById(log.articleId))?.title ||
          '',
        action: log.action,
        content: log.content,
        msg: log.msg,
        createdAt: log.createdAt
          ? dayjs(log.createdAt).tz(TIMEZONE).format('YYYY-MM-DD HH:mm:ss')
          : undefined,
        updatedAt: log.updatedAt
          ? dayjs(log.updatedAt).tz(TIMEZONE).format('YYYY-MM-DD HH:mm:ss')
          : undefined,
      })),
    );
    return { total, list: resultList };
  }
}

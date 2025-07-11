import { Injectable } from '@nestjs/common';
import { InjectModel } from '@nestjs/mongoose';
import { Model, DeleteResult } from 'mongoose';
import { ArticleLog, ArticleLogDocument } from './schema/log.schema';
import { CreateArticleLogDto, QueryArticleLogDto } from './dto';
import { UserService } from '../user/user.service';
import { ArticleService } from '../article/article.service';
import dayjs from 'dayjs';
import utc from 'dayjs/plugin/utc';
import timezone from 'dayjs/plugin/timezone';
import isLeapYear from 'dayjs/plugin/isLeapYear';

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
  ) {}

  async create(dto: CreateArticleLogDto) {
    // 指定 createdAt 为东八区时间
    return this.logModel.create(dto);
  }

  async removeById(id: string) {
    return this.logModel.findByIdAndDelete(id).exec();
  }

  async removeByIds(ids: string[]): Promise<DeleteResult> {
    return this.logModel.deleteMany({ _id: { $in: ids } }).exec();
  }

  async findByFilter(query: QueryArticleLogDto) {
    const {
      userId,
      articleId,
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

    const skip = (parseInt(page) - 1) * parseInt(size);
    const take = parseInt(size);

    const [total, list] = await Promise.all([
      this.logModel.countDocuments(filters),
      this.logModel
        .find(filters)
        .sort({ createdAt: -1 })
        .skip(skip)
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

import { Injectable } from '@nestjs/common';
import { InjectModel } from '@nestjs/mongoose';
import { Model } from 'mongoose';
import { ArticleLog, ArticleLogDocument } from './schema/log.schema';
import { CreateArticleLogDto, QueryArticleLogDto } from './dto';
const dayjs = require('dayjs');

@Injectable()
export class ArticleLogService {
  constructor(
    @InjectModel(ArticleLog.name)
    private readonly logModel: Model<ArticleLogDocument>,
  ) {}

  async create(dto: CreateArticleLogDto) {
    return this.logModel.create(dto);
  }

  async removeById(id: string) {
    return this.logModel.findByIdAndDelete(id).exec();
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

    return { total, list };
  }
}

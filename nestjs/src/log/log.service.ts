import { Injectable } from '@nestjs/common';
import { InjectModel } from '@nestjs/mongoose';
import { Model } from 'mongoose';
import { ArticleLog, ArticleLogDocument } from './schema/log.schema';
import { CreateArticleLogDto } from './dto';

@Injectable()
export class ArticleLogService {
  constructor(
    @InjectModel(ArticleLog.name)
    private readonly logModel: Model<ArticleLogDocument>,
  ) {}

  async create(dto: CreateArticleLogDto) {
    return this.logModel.create(dto);
  }

  async findAll() {
    const [total, list] = await Promise.all([
      this.logModel.countDocuments().exec(),
      this.logModel.find().sort({ createdAt: -1 }).exec(),
    ]);
    return { total, list };
  }

  async findAllByArticle(articleId: string) {
    const [total, list] = await Promise.all([
      this.logModel.countDocuments({ articleId }).exec(),
      this.logModel.find({ articleId }).sort({ createdAt: -1 }).exec(),
    ]);
    return { total, list };
  }

  async findAllByUser(userId: string) {
    const [total, list] = await Promise.all([
      this.logModel.countDocuments({ userId }).exec(),
      this.logModel.find({ userId }).sort({ createdAt: -1 }).exec(),
    ]);
    return { total, list };
  }
}

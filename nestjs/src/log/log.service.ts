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

  async findAll(): Promise<ArticleLog[]> {
    return this.logModel.find().sort({ createdAt: -1 }).exec();
  }

  async findAllByArticle(articleId: string) {
    return this.logModel.find({ articleId }).sort({ createdAt: -1 }).exec();
  }

  async findAllByUser(userId: string) {
    return this.logModel.find({ userId }).sort({ createdAt: -1 }).exec();
  }
}

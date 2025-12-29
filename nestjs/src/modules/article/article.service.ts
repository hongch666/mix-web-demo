import { Injectable } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository, Like } from 'typeorm';
import { Articles } from './entities/article.entity';

@Injectable()
export class ArticleService {
  constructor(
    @InjectRepository(Articles)
    private readonly articleRepository: Repository<Articles>,
  ) {}

  // 查询文章
  async getArticleById(id: number): Promise<Articles | null> {
    return this.articleRepository.findOne({ where: { id } });
  }

  // 根据标题模糊搜索文章
  async getArticlesByTitle(title: string): Promise<Articles[]> {
    return this.articleRepository.find({
      where: { title: Like(`%${title}%`) },
    });
  }
}

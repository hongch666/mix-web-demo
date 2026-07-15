import { Injectable } from "@nestjs/common";
import { InjectRepository } from "@nestjs/typeorm";
import { Like, Repository } from "typeorm";
import { Articles } from "./entities/article.entity";

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

  // 批量查询文章（用于解决 N+1 查询问题）
  async getArticleByIds(ids: number[]): Promise<Articles[]> {
    if (!ids || ids.length === 0) {
      return [];
    }
    return this.articleRepository.find({
      where: ids.map((id) => ({ id })),
    });
  }

  // 根据标题模糊搜索文章
  async getArticlesByTitle(title: string): Promise<Articles[]> {
    return this.articleRepository.find({
      where: { title: Like(`%${title}%`) },
    });
  }
}

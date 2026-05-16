import { Injectable } from '@nestjs/common';
import { SpringClientService } from 'src/modules/client/springClient.service';

export interface RemoteArticle {
  id: number;
  title: string;
  content?: string;
  tags?: string;
  userId?: number;
  username?: string;
  createAt?: string;
  updateAt?: string;
}

@Injectable()
export class ArticleService {
  constructor(private readonly springClientService: SpringClientService) {}

  async getArticleById(id: number): Promise<RemoteArticle | null> {
    const response = await this.springClientService.getArticleById(id);
    return (response.data as RemoteArticle | null) ?? null;
  }

  async getArticlesByIds(ids: number[]): Promise<Map<number, RemoteArticle>> {
    const validIds = Array.from(
      new Set(ids.filter((id) => Number.isFinite(id) && id > 0)),
    );
    if (validIds.length === 0) {
      return new Map();
    }
    const response = await this.springClientService.getArticlesByIds(validIds);
    const articles = (response.data as RemoteArticle[] | null) ?? [];
    return new Map(articles.map((article) => [article.id, article]));
  }

  async getArticlesByTitle(title: string): Promise<RemoteArticle[]> {
    const response = await this.springClientService.searchArticles(title);
    const data = response.data as { list?: RemoteArticle[] } | undefined;
    return data?.list ?? [];
  }
}

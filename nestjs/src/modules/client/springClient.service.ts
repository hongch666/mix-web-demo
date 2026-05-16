import { Injectable } from '@nestjs/common';
import { NacosService } from 'src/modules/nacos/nacos.service';

@Injectable()
export class SpringClientService {
  constructor(private readonly nacosService: NacosService) {}

  async test(): Promise<Record<string, unknown>> {
    return await this.nacosService.call({
      serviceName: 'spring',
      method: 'GET',
      path: '/api_spring/spring',
    });
  }

  async createTokenTicket(
    userId: number,
    username: string,
  ): Promise<Record<string, unknown>> {
    const safeUsername: string = username.replace(/[^\x20-\x7E]/g, '').trim();
    return await this.nacosService.call({
      serviceName: 'spring',
      method: 'POST',
      path: '/users/github/token-ticket',
      body: {
        userId,
        username,
      },
      headers: {
        'X-Username': safeUsername,
      },
    });
  }

  async upsertGithubUser(profile: Record<string, unknown>): Promise<Record<string, unknown>> {
    return await this.nacosService.call({
      serviceName: 'spring',
      method: 'POST',
      path: '/users/github/upsert',
      body: profile,
    });
  }

  async getUserById(userId: number): Promise<Record<string, unknown>> {
    return await this.nacosService.call({
      serviceName: 'spring',
      method: 'GET',
      path: `/users/${userId}`,
    });
  }

  async searchUsers(username: string): Promise<Record<string, unknown>> {
    return await this.nacosService.call({
      serviceName: 'spring',
      method: 'GET',
      path: '/users',
      queryParams: {
        page: '1',
        size: '50',
        username,
      },
    });
  }

  async getUserRole(userId: number): Promise<Record<string, unknown>> {
    return await this.nacosService.call({
      serviceName: 'spring',
      method: 'GET',
      path: `/users/role/${userId}`,
    });
  }

  async getArticleById(articleId: number): Promise<Record<string, unknown>> {
    return await this.nacosService.call({
      serviceName: 'spring',
      method: 'GET',
      path: `/articles/${articleId}`,
    });
  }

  async searchArticles(title: string): Promise<Record<string, unknown>> {
    return await this.nacosService.call({
      serviceName: 'spring',
      method: 'GET',
      path: '/articles/list',
      queryParams: {
        page: '1',
        size: '50',
      },
      headers: {
        'X-Article-Search-Title': title,
      },
    });
  }

  async getUsersByIds(ids: number[]): Promise<Record<string, unknown>> {
    return await this.nacosService.call({
      serviceName: 'spring',
      method: 'POST',
      path: '/users/batch',
      body: { ids },
    });
  }

  async getArticlesByIds(ids: number[]): Promise<Record<string, unknown>> {
    return await this.nacosService.call({
      serviceName: 'spring',
      method: 'POST',
      path: '/articles/batch',
      body: { ids },
    });
  }
}

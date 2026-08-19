import { Injectable } from "@nestjs/common";
import { NacosService } from "../nacos/nacos.service";

/**
 * Spring 服务远程调用客户端
 * 通过 Nacos 服务发现 + 内部令牌认证调用 Spring 内部接口
 */
@Injectable()
export class SpringClientService {
  constructor(private readonly nacosService: NacosService) {}

  /**
   * 从 Spring 统一响应中提取 data 字段
   */
  static extractData<T>(response: Record<string, unknown>): T {
    return (response.data ?? response) as T;
  }

  // ==================== 用户相关 ====================

  /**
   * 根据ID查询用户（复用已有 GET /users/{id} 接口）
   */
  async getUserById(id: number): Promise<Record<string, unknown>> {
    return await this.nacosService.call({
      serviceName: "spring",
      method: "GET",
      path: `/users/${id}`,
    });
  }

  /**
   * 批量查询用户
   */
  async getUserByIds(ids: number[]): Promise<Record<string, unknown>> {
    return await this.nacosService.call({
      serviceName: "spring",
      method: "POST",
      path: "/users/batch",
      body: { ids },
    });
  }

  /**
   * 根据用户名模糊搜索用户
   */
  async getUsersByName(name: string): Promise<Record<string, unknown>> {
    return await this.nacosService.call({
      serviceName: "spring",
      method: "GET",
      path: "/users/by-name",
      queryParams: { name },
    });
  }

  /**
   * 根据GitHub ID查询用户
   */
  async getUserByGithubId(githubId: string): Promise<Record<string, unknown>> {
    return await this.nacosService.call({
      serviceName: "spring",
      method: "GET",
      path: `/users/by-github-id/${githubId}`,
    });
  }

  /**
   * 创建或更新GitHub用户
   */
  async findOrCreateGithubUser(
    dto: Record<string, unknown>,
  ): Promise<Record<string, unknown>> {
    return await this.nacosService.call({
      serviceName: "spring",
      method: "POST",
      path: "/users/github-user",
      body: dto,
    });
  }

  /**
   * 判断用户是否为管理员
   */
  async isAdminUser(userId: number): Promise<Record<string, unknown>> {
    return await this.nacosService.call({
      serviceName: "spring",
      method: "GET",
      path: `/users/${userId}/is-admin`,
    });
  }

  /**
   * 生成GitHub登录票据（已有接口）
   */
  async createTokenTicket(
    userId: number,
    username: string,
  ): Promise<Record<string, unknown>> {
    const safeUsername: string = username.replace(/[^\x20-\x7E]/g, "").trim();
    return await this.nacosService.call({
      serviceName: "spring",
      method: "POST",
      path: "/users/github/token-ticket",
      body: {
        user_id: userId,
        username,
      },
      headers: {
        "X-Username": safeUsername,
      },
    });
  }

  // ==================== 文章相关 ====================

  /**
   * 根据ID查询文章（复用已有 GET /articles/{id} 接口）
   */
  async getArticleById(id: number): Promise<Record<string, unknown>> {
    return await this.nacosService.call({
      serviceName: "spring",
      method: "GET",
      path: `/articles/${id}`,
    });
  }

  /**
   * 批量查询文章
   */
  async getArticleByIds(ids: number[]): Promise<Record<string, unknown>> {
    return await this.nacosService.call({
      serviceName: "spring",
      method: "POST",
      path: "/articles/batch",
      body: { ids },
    });
  }

  /**
   * 根据标题模糊搜索文章
   */
  async getArticlesByTitle(title: string): Promise<Record<string, unknown>> {
    return await this.nacosService.call({
      serviceName: "spring",
      method: "GET",
      path: "/articles/by-title",
      queryParams: { title },
    });
  }
}

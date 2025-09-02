import { Injectable } from '@nestjs/common';
import { NacosService } from 'src/common/nacos/nacos.service';
const marked = require('marked');
const dayjs = require('dayjs');

@Injectable()
export class ArticleService {
  constructor(private readonly nacosService: NacosService) {}

  // 查询文章
  async getArticleById(id: number): Promise<any> {
    // 调用Spring接口获取文章数据
    const res = await this.nacosService.call({
      serviceName: 'spring',
      method: 'GET',
      path: `/articles/:id`,
      pathParams: { id: id.toString() },
    });
    const article = res.data;
    return article;
  }

  // 根据标题模糊搜索文章
  async getArticlesByTitle(title: string): Promise<any[]> {
    // 调用Spring接口获取文章数据
    const res = await this.nacosService.call({
      serviceName: 'spring',
      method: 'GET',
      path: '/articles/list',
      queryParams: {
        title,
      },
    });
    const articles = res.data.list;

    return articles;
  }
}

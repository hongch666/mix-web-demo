import { Injectable } from '@nestjs/common';
import * as fs from 'fs';
import * as path from 'path';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository, Like } from 'typeorm';
import { Articles } from './entities/article.entity';
import { WordService } from 'src/common/word/word.service';
import { NacosService } from 'src/common/nacos/nacos.service';
import { ConfigService } from '@nestjs/config';

@Injectable()
export class ArticleService {
  constructor(
    @InjectRepository(Articles)
    private readonly articleRepository: Repository<Articles>,
    private readonly wordService: WordService,
    private readonly nacosService: NacosService,
    private readonly configService: ConfigService,
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

  // 生成word并保存到指定位置
  async exportToWordAndSave(id: number) {
    const article = await this.getArticleById(id);
    if (!article) {
      throw new Error(`Article with id ${id} not found`);
    }
    const data = {
      title: article.title,
      content: article.content,
      tags: article.tags,
    };
    const filePath = this.configService.get<string>('files.word'); // 获取配置中的模板路径
    if (!filePath) {
      throw new Error('Word template file path is not configured');
    }
    const templatePath = path.join(process.cwd(), filePath, 'template.docx'); // 模板文件路径
    const savePath = path.join(process.cwd(), filePath, `article-${id}.docx`); // 保存路径
    // 调用 WordService 生成并保存 Word 文档
    const buffer = await this.wordService.exportToWord(data, templatePath);
    // 确保保存目录存在
    if (!fs.existsSync(path.dirname(savePath))) {
      fs.mkdirSync(path.dirname(savePath), { recursive: true });
    }
    // 保存文件到指定路径
    fs.writeFileSync(savePath, buffer);
    const url = await this.uploadWordToOSS(
      savePath,
      `articles/article-${id}.docx`,
    );
    // 返回保存路径
    return url;
  }

  // 上传Word文件到OSS
  async uploadWordToOSS(filePath: string, ossPath: string) {
    const res = await this.nacosService.call({
      serviceName: 'fastapi',
      method: 'POST',
      path: '/upload',
      body: {
        local_file: filePath,
        oss_file: ossPath,
      },
    });
    return res.data;
  }
}

import { Injectable } from '@nestjs/common';
import * as fs from 'fs';
import * as path from 'path';
import { createReport } from 'docx-templates';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { Articles } from './entities/article.entity';
import { WordService } from 'src/word/word.service';
import { NacosService } from 'src/nacos/nacos.service';

@Injectable()
export class ArticleService {
  constructor(
    @InjectRepository(Articles)
    private readonly articleRepository: Repository<Articles>,
    private readonly wordService: WordService,
    private readonly nacosService: NacosService,
  ) {}

  // 查询文章
  async getArticleById(id: number): Promise<Articles | null> {
    return this.articleRepository.findOne({ where: { id } });
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
    const templatePath = 'files/template.docx'; // 模板文件路径
    const savePath = `files/article-${id}.docx`; // 保存路径
    // 调用 WordService 生成并保存 Word 文档
    const buffer = await this.wordService.exportToWord(data, templatePath);
    // 确保保存目录存在
    if (!fs.existsSync(path.dirname(savePath))) {
      fs.mkdirSync(path.dirname(savePath), { recursive: true });
    }
    // 保存文件到指定路径
    fs.writeFileSync(savePath, buffer);
    const url = await this.uploadWordToOSS(
      path.join('nestjs', savePath),
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

import { Injectable } from '@nestjs/common';
import * as fs from 'fs';
import * as path from 'path';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository, Like } from 'typeorm';
import { Articles } from './entities/article.entity';
import { WordService } from 'src/common/word/word.service';
import { NacosService } from 'src/common/nacos/nacos.service';
import { ConfigService } from '@nestjs/config';
import { marked } from 'marked';
import { User } from '../user/entities/user.entity';
const dayjs = require('dayjs');

@Injectable()
export class ArticleService {
  constructor(
    @InjectRepository(Articles)
    private readonly articleRepository: Repository<Articles>,
    @InjectRepository(User)
    private readonly userRepository: Repository<User>,
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
    // 将markdown内容转为html
    const htmlContent = marked.parse(article.content || '');
    const data = {
      title: article.title,
      // 传递htmlContent给word模板
      content: htmlContent,
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
    const url = await this.uploadFileToOSS(
      savePath,
      `articles/article-${id}.docx`,
    );
    // 返回保存路径
    return url;
  }

  // 生成markdown文件并上传到OSS，返回下载链接
  async exportMarkdownAndUpload(id: number): Promise<string> {
    const article = await this.getArticleById(id);
    if (!article) {
      throw new Error(`Article with id ${id} not found`);
    }
    // 拼接markdown内容
    let markdown = `# ${article.title}\n`;
    markdown += `\n**标签：** ${article.tags}\n`;
    const user = await this.userRepository.findOne({
      where: { id: article.user_id },
    });
    markdown += `\n**作者：** ${user?.name || '未知'}\n`;
    markdown += `\n---\n`;
    markdown += article.content || '';
    markdown += `\n---\n`;
    markdown += `\n**创建时间：** ${dayjs(article.create_at).format('YYYY-MM-DD HH:mm:ss')}\n`;
    markdown += `\n**更新时间：** ${dayjs(article.update_at).format('YYYY-MM-DD HH:mm:ss')}\n`;
    // 保存到本地临时文件
    const filePath = this.configService.get<string>('files.word') || 'static';
    const saveDir = path.join(process.cwd(), filePath);
    if (!fs.existsSync(saveDir)) {
      fs.mkdirSync(saveDir, { recursive: true });
    }
    const savePath = path.join(saveDir, `article-${id}.md`);
    fs.writeFileSync(savePath, markdown);
    // 上传到OSS
    const ossPath = `articles/article-${id}.md`;
    const url = await this.uploadFileToOSS(savePath, ossPath);
    return url;
  }

  // 上传Word文件到OSS
  async uploadFileToOSS(filePath: string, ossPath: string) {
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

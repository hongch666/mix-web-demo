import { Injectable } from '@nestjs/common';
import * as fs from 'fs';
import * as path from 'path';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository, Like } from 'typeorm';
import { Articles } from './entities/article.entity';
import { WordService } from 'src/modules/word/word.service';
import { NacosService } from 'src/modules/nacos/nacos.service';
import { ConfigService } from '@nestjs/config';
import { User } from '../user/entities/user.entity';
import { fileLogger } from 'src/common/utils/writeLog';
import * as puppeteer from 'puppeteer';
const marked = require('marked');
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
    const htmlContent = marked.parse(article.content || '');
    const user = await this.userRepository.findOne({
      where: { id: article.user_id },
    });
    const data = {
      title: article.title,
      // 传递htmlContent给word模板
      content: htmlContent,
      tags: article.tags,
      username: user?.name || '未知',
      create_at: dayjs(article.create_at).format('YYYY-MM-DD HH:mm:ss'),
      update_at: dayjs(article.update_at).format('YYYY-MM-DD HH:mm:ss'),
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
    // 上传后删除本地Word文件
    try {
      fs.unlinkSync(savePath);
    } catch (e) {
      fileLogger.error(
        '删除文章Word文件失败' + (e.message ? e.message : '未知错误'),
      );
    }
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
    // 上传后删除本地Markdown文件
    try {
      fs.unlinkSync(savePath);
    } catch (e) {
      fileLogger.error(
        '删除文章Markdown文件失败' + (e.message ? e.message : '未知错误'),
      );
    }
    return url;
  }

  // 生成PDF文件并保存到指定位置
  async exportToPdfAndSave(id: number): Promise<string> {
    const article = await this.getArticleById(id);
    if (!article) {
      throw new Error(`Article with id ${id} not found`);
    }

    const user = await this.userRepository.findOne({
      where: { id: article.user_id },
    });

    // 获取文件保存路径
    const filePath = this.configService.get<string>('files.word') || 'static';
    const saveDir = path.join(process.cwd(), filePath);
    if (!fs.existsSync(saveDir)) {
      fs.mkdirSync(saveDir, { recursive: true });
    }
    const savePath = path.join(saveDir, `article-${id}.pdf`);

    // 创建 HTML 内容
    const htmlContent = this.generatePdfHtml(
      article,
      user || ({ name: '未知' } as User),
    );

    // 使用 puppeteer 生成 PDF
    let browser;
    try {
      browser = await puppeteer.launch({
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox'],
      });

      const page = await browser.newPage();
      await page.setContent(htmlContent, { waitUntil: 'networkidle0' });

      // 生成 PDF
      await page.pdf({
        path: savePath,
        format: 'A4',
        margin: {
          top: '20mm',
          bottom: '20mm',
          left: '20mm',
          right: '20mm',
        },
      });

      await page.close();
      await browser.close();

      // 上传到 OSS
      const ossPath = `articles/article-${id}.pdf`;
      const url = await this.uploadFileToOSS(savePath, ossPath);

      // 删除本地 PDF 文件
      try {
        fs.unlinkSync(savePath);
      } catch (e) {
        fileLogger.error(
          '删除文章PDF文件失败' + (e.message ? e.message : '未知错误'),
        );
      }

      return url;
    } catch (error) {
      fileLogger.error(
        '生成PDF失败: ' + (error.message ? error.message : '未知错误'),
      );
      throw error;
    }
  }

  // 生成 PDF 的 HTML 内容
  private generatePdfHtml(article: Articles, user: User): string {
    const createTime = dayjs(article.create_at).format('YYYY-MM-DD HH:mm:ss');
    const updateTime = dayjs(article.update_at).format('YYYY-MM-DD HH:mm:ss');
    const generateTime = dayjs().format('YYYY-MM-DD HH:mm:ss');

    return `
      <!DOCTYPE html>
      <html lang="zh-CN">
      <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>${article.title}</title>
        <style>
          * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
          }
          body {
            font-family: 'Segoe UI', 'SimSun', '微软雅黑', '宋体', sans-serif;
            line-height: 1.8;
            color: #333;
            background: white;
          }
          .container {
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
          }
          .title {
            font-size: 28px;
            font-weight: bold;
            text-align: center;
            margin-bottom: 20px;
            text-decoration: underline;
            color: #000;
          }
          .meta-info {
            text-align: center;
            font-size: 12px;
            color: #666;
            margin-bottom: 10px;
            line-height: 1.6;
          }
          .tags {
            text-align: center;
            font-size: 12px;
            color: #0066cc;
            margin-bottom: 20px;
          }
          .divider {
            border-top: 1px solid #999;
            margin: 20px 0;
          }
          .content {
            font-size: 14px;
            line-height: 1.8;
            margin-bottom: 30px;
            white-space: pre-wrap;
            word-break: break-all;
          }
          .footer {
            text-align: center;
            font-size: 11px;
            color: #999;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
          }
          code {
            background-color: #f5f5f5;
            padding: 2px 4px;
            border-radius: 2px;
            font-family: 'Courier New', monospace;
          }
          pre {
            background-color: #f5f5f5;
            padding: 10px;
            border-radius: 4px;
            overflow-x: auto;
            margin: 10px 0;
          }
        </style>
      </head>
      <body>
        <div class="container">
          <div class="title">${article.title}</div>
          
          <div class="meta-info">
            <div>作者: ${user?.name || '未知'}</div>
            <div>创建于: ${createTime}</div>
            <div>更新于: ${updateTime}</div>
          </div>
          
          ${article.tags ? `<div class="tags">标签: ${article.tags}</div>` : ''}
          
          <div class="divider"></div>
          
          <div class="content">${(article.content || '').replace(/</g, '&lt;').replace(/>/g, '&gt;')}</div>
          
          <div class="footer">
            <div>---</div>
            <div>生成时间: ${generateTime} | 文章ID: ${article.id}</div>
          </div>
        </div>
      </body>
      </html>
    `;
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

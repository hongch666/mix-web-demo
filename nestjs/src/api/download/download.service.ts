import { Injectable } from '@nestjs/common';
import * as fs from 'fs';
import * as path from 'path';
import { WordService } from 'src/modules/word/word.service';
import { NacosService } from 'src/modules/nacos/nacos.service';
import { ConfigService } from '@nestjs/config';
import { logger } from 'src/common/utils/writeLog';
import * as puppeteer from 'puppeteer';
import { UserService } from 'src/modules/user/user.service';
import { ArticleService } from 'src/modules/article/article.service';
import { User } from 'src/modules/user/entities/user.entity';
import { Articles } from 'src/modules/article/entities/article.entity';
import * as marked from 'marked';
import dayjs from 'dayjs';
import { BusinessException } from 'src/common/exceptions/business.exception';
import { Constants } from 'src/common/utils/constants';

@Injectable()
export class DownloadService {
  constructor(
    private readonly userService: UserService,
    private readonly articleService: ArticleService,
    private readonly wordService: WordService,
    private readonly nacosService: NacosService,
    private readonly configService: ConfigService,
  ) {}

  // 生成word并保存到指定位置
  async exportToWordAndSave(id: number): Promise<string> {
    const article: Articles | null = await this.articleService.getArticleById(id);
    if (!article) {
      throw new BusinessException(`文章 ID ${id} 未找到`);
    }
    const htmlContent: string = marked.parse(article.content || '') as string;
    const user: User | null = await this.userService.getUserById(article.user_id);
    const data: Record<string, any> = {
      title: article.title,
      // 传递htmlContent给word模板
      content: htmlContent,
      tags: article.tags,
      username: user?.name || Constants.UNKNOWN_USER,
      create_at: dayjs(article.create_at).format('YYYY-MM-DD HH:mm:ss'),
      update_at: dayjs(article.update_at).format('YYYY-MM-DD HH:mm:ss'),
    };
    const filePath: string | undefined = this.configService.get<string>('files.word'); // 获取配置中的模板路径
    if (!filePath) {
      throw new BusinessException(Constants.EMPTY_FILE_PATH);
    }
    const templatePath: string = path.join(process.cwd(), filePath, 'template.docx'); // 模板文件路径
    const savePath: string = path.join(process.cwd(), filePath, `article-${id}.docx`); // 保存路径
    // 调用 WordService 生成并保存 Word 文档
    const buffer: Buffer = await this.wordService.exportToWord(data, templatePath);
    // 确保保存目录存在
    if (!fs.existsSync(path.dirname(savePath))) {
      fs.mkdirSync(path.dirname(savePath), { recursive: true });
    }
    // 保存文件到指定路径
    fs.writeFileSync(savePath, buffer);
    const url: string = await this.uploadFileToOSS(
      savePath,
      `articles/article-${id}.docx`,
    );
    // 上传后删除本地Word文件
    fs.unlinkSync(savePath);
    return url;
  }

  // 生成markdown文件并上传到OSS，返回下载链接
  async exportMarkdownAndUpload(id: number): Promise<string> {
    const article: Articles | null = await this.articleService.getArticleById(id);
    if (!article) {
      throw new BusinessException(`文章 ID ${id} 未找到`);
    }
    // 拼接markdown内容
    let markdown: string = `# ${article.title}\n`;
    markdown += `\n**标签：** ${article.tags}\n`;
    const user: User | null = await this.userService.getUserById(article.user_id);
    markdown += `\n**作者：** ${user?.name || '未知'}\n`;
    markdown += `\n**创作时间：** ${dayjs(article.create_at).format('YYYY-MM-DD HH:mm:ss')}\n`;
    markdown += `\n---\n`;
    markdown += article.content || '';
    // 保存到本地临时文件
    const filePath: string = this.configService.get<string>('files.word') || 'static';
    const saveDir: string = path.join(process.cwd(), filePath);
    if (!fs.existsSync(saveDir)) {
      fs.mkdirSync(saveDir, { recursive: true });
    }
    const savePath: string = path.join(saveDir, `article-${id}.md`);
    fs.writeFileSync(savePath, markdown);
    // 上传到OSS
    const ossPath: string = `articles/article-${id}.md`;
    const url: string = await this.uploadFileToOSS(savePath, ossPath);
    // 上传后删除本地Markdown文件
    fs.unlinkSync(savePath);
    return url;
  }

  // 生成PDF文件并保存到指定位置
  async exportToPdfAndSave(id: number): Promise<string> {
    const article: Articles | null = await this.articleService.getArticleById(id);
    if (!article) {
      throw new BusinessException(`文章 ID ${id} 未找到`);
    }

    const user: User | null = await this.userService.getUserById(article.user_id);

    // 获取文件保存路径
    const filePath: string = this.configService.get<string>('files.word') || 'static';
    const saveDir: string = path.join(process.cwd(), filePath);
    if (!fs.existsSync(saveDir)) {
      fs.mkdirSync(saveDir, { recursive: true });
    }
    const savePath: string = path.join(saveDir, `article-${id}.pdf`);

    // 创建 HTML 内容
    const htmlContent: string = this.generatePdfHtml(
      article,
      user || ({ name: '未知' } as User),
    );

    // 使用 puppeteer 生成 PDF
    let browser: puppeteer.Browser;
    browser = await puppeteer.launch({
      headless: true,
      args: ['--no-sandbox', '--disable-setuid-sandbox'],
    });

    const page: puppeteer.Page = await browser.newPage();
    await page.setContent(htmlContent, { waitUntil: 'networkidle0' });

    // 生成 PDF
    await page.pdf({
      path: savePath,
      format: 'A4',
      margin: {
        top: '15mm',
        bottom: '15mm',
        left: '15mm',
        right: '15mm',
      },
      printBackground: true,
    });

    await page.close();
    await browser.close();

    // 上传到 OSS
    const ossPath: string = `articles/article-${id}.pdf`;
    const url: string = await this.uploadFileToOSS(savePath, ossPath);

    // 删除本地 PDF 文件
    fs.unlinkSync(savePath);

    return url;
  }

  // 生成 PDF 的 HTML 内容
  private generatePdfHtml(article: Articles, user: User): string {
    const createTime: string = dayjs(article.create_at).format('YYYY-MM-DD HH:mm:ss');
    const updateTime: string = dayjs(article.update_at).format('YYYY-MM-DD HH:mm:ss');
    const generateTime: string = dayjs().format('YYYY-MM-DD HH:mm:ss');

    // 使用 marked 解析 Markdown 内容为 HTML
    const htmlContent: string = marked.parse(article.content || '') as string;

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
          html, body {
            margin: 0;
            padding: 0;
            height: auto;
          }
          body {
            font-family: 'Segoe UI', 'SimSun', '微软雅黑', '宋体', sans-serif;
            line-height: 1.8;
            color: #333;
            background: white;
          }
          @page {
            size: A4;
            margin: 15mm 15mm 15mm 15mm;
          }
          .container {
            max-width: 100%;
            margin: 0;
            padding: 0;
          }
          .title {
            font-size: 24px;
            font-weight: bold;
            text-align: center;
            margin-bottom: 12px;
            color: #000;
          }
          .meta-info {
            text-align: center;
            font-size: 11px;
            color: #666;
            margin-bottom: 8px;
            line-height: 1.4;
          }
          .tags {
            text-align: center;
            font-size: 11px;
            color: #0066cc;
            margin-bottom: 12px;
          }
          .divider {
            border-top: 1px solid #999;
            margin: 12px 0;
          }
          .content {
            font-size: 14px;
            line-height: 1.8;
            margin-bottom: 10px;
          }
          .content h1 {
            font-size: 22px;
            font-weight: bold;
            margin: 12px 0 6px 0;
          }
          .content h2 {
            font-size: 18px;
            font-weight: bold;
            margin: 10px 0 6px 0;
            border-bottom: 1px solid #ddd;
            padding-bottom: 3px;
          }
          .content h3 {
            font-size: 16px;
            font-weight: bold;
            margin: 10px 0 4px 0;
          }
          .content h4,
          .content h5,
          .content h6 {
            font-size: 14px;
            font-weight: bold;
            margin: 8px 0 4px 0;
          }
          .content p {
            margin: 4px 0;
            text-align: justify;
          }
          .content ul,
          .content ol {
            margin: 6px 0 6px 20px;
          }
          .content li {
            margin: 2px 0;
          }
          .content blockquote {
            border-left: 4px solid #d0d0d0;
            margin: 6px 0;
            padding-left: 12px;
            color: #666;
            font-size: 13px;
          }
          .content code {
            background-color: #f5f5f5;
            padding: 1px 4px;
            border-radius: 2px;
            font-family: 'Courier New', 'Consolas', monospace;
            font-size: 12px;
          }
          .content pre {
            background-color: #f8f8f8;
            border: 1px solid #ddd;
            padding: 8px;
            border-radius: 3px;
            overflow-x: auto;
            margin: 8px 0;
            line-height: 1.3;
            font-size: 11px;
          }
          .content pre code {
            background-color: transparent;
            padding: 0;
            border-radius: 0;
            font-size: 11px;
          }
          .content table {
            border-collapse: collapse;
            margin: 8px 0;
            width: 100%;
            font-size: 12px;
          }
          .content table th,
          .content table td {
            border: 1px solid #ddd;
            padding: 4px 6px;
            text-align: left;
          }
          .content table th {
            background-color: #f5f5f5;
            font-weight: bold;
          }
          .content hr {
            border: none;
            border-top: 1px solid #ddd;
            margin: 10px 0;
          }
          .footer {
            text-align: center;
            font-size: 10px;
            color: #666;
            margin-top: 12px;
            padding: 10px 12px;
            border-top: 1px solid #e0e0e0;
            background-color: #f9f9f9;
            line-height: 1.6;
          }
          .footer-line {
            font-size: 11px;
            color: #555;
            font-weight: 500;
          }
          .footer-detail {
            font-size: 9px;
            color: #999;
            margin-top: 4px;
          }
        </style>
      </head>
      <body>
        <div class="container">
          <div class="title">${article.title}</div>
          
          <div class="meta-info">
            <div>作者: ${user?.name || '未知'}</div>
            <div>创作时间: ${createTime}</div>
          </div>
          
          ${article.tags ? `<div class="tags">标签: ${article.tags}</div>` : ''}
          
          <div class="divider"></div>
          
          <div class="content">${htmlContent}</div>
          
        </div>
      </body>
      </html>
    `;
  }

  // 上传Word文件到OSS
  async uploadFileToOSS(filePath: string, ossPath: string): Promise<string> {
    try {
      const res: any = await this.nacosService.call({
        serviceName: 'fastapi',
        method: 'POST',
        path: '/upload',
        body: {
          local_file: filePath,
          oss_file: ossPath,
        },
      });
      return res.data;
    } catch (error: any) {
      logger.error(`上传阿里云OSS错误: ${error.message}`);
      throw new BusinessException(Constants.OSS_UPLOAD_ERR);
    }
  }
}

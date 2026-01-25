import { Injectable } from '@nestjs/common';
import * as fs from 'fs';
import * as path from 'path';
import { WordService } from 'src/modules/word/word.service';
import { NacosService } from 'src/modules/nacos/nacos.service';
import { ConfigService } from '@nestjs/config';
import { fileLogger } from 'src/common/utils/writeLog';
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
  async exportToWordAndSave(id: number) {
    const article = await this.articleService.getArticleById(id);
    if (!article) {
      throw new BusinessException(`文章 ID ${id} 未找到`);
    }
    const htmlContent = marked.parse(article.content || '');
    const user = await this.userService.getUserById(article.user_id);
    const data = {
      title: article.title,
      // 传递htmlContent给word模板
      content: htmlContent,
      tags: article.tags,
      username: user?.name || Constants.UNKNOWN_USER,
      create_at: dayjs(article.create_at).format('YYYY-MM-DD HH:mm:ss'),
      update_at: dayjs(article.update_at).format('YYYY-MM-DD HH:mm:ss'),
    };
    const filePath = this.configService.get<string>('files.word'); // 获取配置中的模板路径
    if (!filePath) {
      throw new BusinessException(Constants.EMPTY_FILE_PATH);
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
    fs.unlinkSync(savePath);
    return url;
  }

  // 生成markdown文件并上传到OSS，返回下载链接
  async exportMarkdownAndUpload(id: number): Promise<string> {
    const article = await this.articleService.getArticleById(id);
    if (!article) {
      throw new BusinessException(`文章 ID ${id} 未找到`);
    }
    // 拼接markdown内容
    let markdown = `# ${article.title}\n`;
    markdown += `\n**标签：** ${article.tags}\n`;
    const user = await this.userService.getUserById(article.user_id);
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
    fs.unlinkSync(savePath);
    return url;
  }

  // 生成PDF文件并保存到指定位置
  async exportToPdfAndSave(id: number): Promise<string> {
    const article = await this.articleService.getArticleById(id);
    if (!article) {
      throw new BusinessException(`文章 ID ${id} 未找到`);
    }

    const user = await this.userService.getUserById(article.user_id);

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
    let browser: puppeteer.Browser;
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
    fs.unlinkSync(savePath);

    return url;
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
    try {
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
    } catch (error) {
      fileLogger.error(`上传阿里云OSS错误: ${error.message}`);
      throw new BusinessException(Constants.OSS_UPLOAD_ERR);
    }
  }
}

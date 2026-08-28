import { Injectable } from "@nestjs/common";
import { ConfigService } from "@nestjs/config";
import dayjs from "dayjs";
import * as fs from "fs";
import * as marked from "marked";
import * as path from "path";
import { Browser, launch, Page } from "puppeteer";
import { ErrorIds, Messages, PdfTemplate } from "src/common/constants";
import { BusinessException } from "src/common/exceptions/business.exception";
import { SpringClientService } from "src/module/common/client/springClient.service";
import { LoggerService } from "src/module/common/logger/logger.service";
import { OssService } from "src/module/common/oss/oss.service";
import { WordService } from "src/module/common/word/word.service";

/**
 * 远程返回的文章数据结构
 */
interface RemoteArticle {
  id: number;
  title: string;
  content: string;
  user_id: number;
  username: string;
  tags: string;
  status: number;
  views: number;
  create_at: string | null;
  update_at: string | null;
}

/**
 * 远程返回的用户数据结构
 */
interface RemoteUser {
  id: number;
  name: string;
}

@Injectable()
export class DownloadService {
  constructor(
    private readonly springClient: SpringClientService,
    private readonly wordService: WordService,
    private readonly ossService: OssService,
    private readonly configService: ConfigService,
    private readonly logger: LoggerService,
  ) {}

  // 生成word并保存到指定位置
  async exportToWordAndSave(id: number): Promise<string> {
    const res: Record<string, unknown> =
      await this.springClient.getArticleById(id);
    const article: RemoteArticle | null =
      SpringClientService.extractData<RemoteArticle | null>(res);
    if (!article) {
      throw BusinessException.notFound(
        Messages.ARTICLE_NOT_FOUND_BY_ID(id),
        ErrorIds.ARTICLE_NOT_FOUND,
      );
    }
    const htmlContent: string = marked.parse(article.content || "");

    // 并行获取用户信息；文章未关联作者（user_id 为空）时跳过，避免调用 GET /users/null 触发 spring 路径变量类型转换 400
    const [userRes] = await Promise.all([
      article.user_id != null
        ? this.springClient.getUserById(article.user_id)
        : Promise.resolve(null),
    ]);
    const user: RemoteUser | null = userRes
      ? SpringClientService.extractData<RemoteUser | null>(userRes)
      : null;

    const data: Record<string, unknown> = {
      title: article.title,
      content: htmlContent,
      tags: article.tags,
      username: user?.name || Messages.UNKNOWN_USER,
      create_at: article.create_at
        ? dayjs(article.create_at).format("YYYY-MM-DD HH:mm:ss")
        : "",
      update_at: article.update_at
        ? dayjs(article.update_at).format("YYYY-MM-DD HH:mm:ss")
        : "",
    };
    const filePath: string | undefined =
      this.configService.get<string>("files.word"); // 获取配置中的模板路径
    if (!filePath) {
      throw BusinessException.notFound(
        Messages.EMPTY_FILE_PATH,
        ErrorIds.EMPTY_FILE_PATH,
      );
    }
    const templatePath: string = path.join(
      process.cwd(),
      filePath,
      "template.docx",
    ); // 模板文件路径
    const savePath: string = path.join(
      process.cwd(),
      filePath,
      `article-${id}.docx`,
    ); // 保存路径
    // 调用 WordService 生成并保存 Word 文档
    const buffer: Buffer = await this.wordService.exportToWord(
      data,
      templatePath,
    );
    // 确保保存目录存在
    await fs.promises.mkdir(path.dirname(savePath), { recursive: true });
    // 保存文件到指定路径
    await fs.promises.writeFile(savePath, buffer);
    try {
      return await this.uploadFileToOSS(
        savePath,
        `articles/article-${id}.docx`,
      );
    } finally {
      await fs.promises.unlink(savePath).catch(() => undefined);
    }
  }

  // 生成markdown文件并上传到OSS，返回下载链接
  async exportMarkdownAndUpload(id: number): Promise<string> {
    const res: Record<string, unknown> =
      await this.springClient.getArticleById(id);
    const article: RemoteArticle | null =
      SpringClientService.extractData<RemoteArticle | null>(res);
    if (!article) {
      throw BusinessException.notFound(
        Messages.ARTICLE_NOT_FOUND_BY_ID(id),
        ErrorIds.ARTICLE_NOT_FOUND,
      );
    }
    // 拼接markdown内容
    let markdown: string = `# ${article.title}\n`;
    markdown += `\n**标签：** ${article.tags}\n`;
    const userRes: Record<string, unknown> =
      await this.springClient.getUserById(article.user_id);
    const user: RemoteUser | null =
      SpringClientService.extractData<RemoteUser | null>(userRes);
    markdown += `\n**作者：** ${user?.name || "未知"}\n`;
    markdown += `\n**创作时间：** ${article.create_at ? dayjs(article.create_at).format("YYYY-MM-DD HH:mm:ss") : ""}\n`;
    markdown += "\n---\n";
    markdown += article.content || "";
    // 保存到本地临时文件
    const filePath: string = this.configService.get<string>("files.word")!;
    if (!filePath) {
      throw BusinessException.internalServerError(
        Messages.WORD_FILE_PATH_NOT_CONFIGURED,
      );
    }
    const saveDir: string = path.join(process.cwd(), filePath);
    await fs.promises.mkdir(saveDir, { recursive: true });
    const savePath: string = path.join(saveDir, `article-${id}.md`);
    await fs.promises.writeFile(savePath, markdown, "utf8");
    try {
      return await this.uploadFileToOSS(savePath, `articles/article-${id}.md`);
    } finally {
      await fs.promises.unlink(savePath).catch(() => undefined);
    }
  }

  // 生成PDF文件并保存到指定位置
  async exportToPdfAndSave(id: number): Promise<string> {
    const res: Record<string, unknown> =
      await this.springClient.getArticleById(id);
    const article: RemoteArticle | null =
      SpringClientService.extractData<RemoteArticle | null>(res);
    if (!article) {
      throw BusinessException.notFound(
        Messages.ARTICLE_NOT_FOUND_BY_ID(id),
        ErrorIds.ARTICLE_NOT_FOUND,
      );
    }

    const userRes: Record<string, unknown> =
      await this.springClient.getUserById(article.user_id);
    const user: RemoteUser | null =
      SpringClientService.extractData<RemoteUser | null>(userRes);

    // 获取文件保存路径
    const filePath: string = this.configService.get<string>("files.word")!;
    if (!filePath) {
      throw BusinessException.internalServerError(
        Messages.WORD_FILE_PATH_NOT_CONFIGURED,
      );
    }
    const saveDir: string = path.join(process.cwd(), filePath);
    await fs.promises.mkdir(saveDir, { recursive: true });
    const savePath: string = path.join(saveDir, `article-${id}.pdf`);

    // 创建 HTML 内容
    const htmlContent: string = this.generatePdfHtml(
      article,
      user || { name: "未知" },
    );

    // 使用 puppeteer 生成 PDF
    const browser: Browser = await launch({
      headless: true,
      args: ["--no-sandbox", "--disable-setuid-sandbox"],
    });

    try {
      const page: Page = await browser.newPage();
      try {
        await page.setContent(htmlContent, { waitUntil: "networkidle0" });
        await page.pdf({
          path: savePath,
          format: PdfTemplate.PAGE_SIZE,
          margin: {
            top: PdfTemplate.PAGE_MARGIN,
            bottom: PdfTemplate.PAGE_MARGIN,
            left: PdfTemplate.PAGE_MARGIN,
            right: PdfTemplate.PAGE_MARGIN,
          },
          printBackground: true,
        });
      } finally {
        await page.close();
      }

      return await this.uploadFileToOSS(savePath, `articles/article-${id}.pdf`);
    } finally {
      await browser.close();
      await fs.promises.unlink(savePath).catch(() => undefined);
    }
  }

  // 生成 PDF 的 HTML 内容
  private generatePdfHtml(
    article: RemoteArticle,
    user: RemoteUser | { name: string },
  ): string {
    const createTime: string = article.create_at
      ? dayjs(article.create_at).format("YYYY-MM-DD HH:mm:ss")
      : "";

    // 使用 marked 解析 Markdown 内容为 HTML
    const htmlContent: string = marked.parse(article.content || "");

    // 模板与样式统一由 PdfTemplate 常量类提供
    return PdfTemplate.renderArticleHtml(
      article.title,
      user?.name,
      createTime,
      article.tags,
      htmlContent,
    );
  }

  // 上传Word文件到OSS
  async uploadFileToOSS(filePath: string, ossPath: string): Promise<string> {
    try {
      const url: string = await this.ossService.uploadFile(filePath, ossPath);
      return url;
    } catch (error: unknown) {
      const message: string =
        error instanceof Error ? error.message : String(error);
      this.logger.error(Messages.OSS_UPLOAD_ERROR_MESSAGE(message));
      throw BusinessException.internalServerError(
        Messages.OSS_UPLOAD_ERR,
        ErrorIds.OSS_UPLOAD_ERROR,
      );
    }
  }
}

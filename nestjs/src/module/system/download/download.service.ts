import { Injectable } from "@nestjs/common";
import { ConfigService } from "@nestjs/config";
import dayjs from "dayjs";
import * as fs from "fs";
import * as marked from "marked";
import * as os from "os";
import * as path from "path";
import { Browser, launch, Page } from "puppeteer";
import { ErrorIds, ExportTemplate, Messages } from "src/common/constants";
import { BusinessException } from "src/common/exceptions";
import type { ArticleExportMeta } from "src/common/interfaces";
import { SpringClientService } from "src/module/common/client";
import { LoggerService } from "src/module/common/logger";
import { OssService } from "src/module/common/oss";
import { WordService } from "src/module/common/word";

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
  category_name: string | null;
  sub_category_name: string | null;
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

/**
 * 导出中间文件目录：文档生成后立即上传 OSS 并删除，落在系统临时目录，不依赖静态目录的写权限
 */
const EXPORT_TEMP_DIR: string = path.join(
  os.tmpdir(),
  "mix-web-demo",
  "export",
);

/** 已发布状态值，与 spring 的 articles.status 约定一致 */
const ARTICLE_STATUS_PUBLISHED = 1;
/** 已发布状态的展示文案 */
const ARTICLE_STATUS_PUBLISHED_TEXT = "已发布";
/** 非发布状态（含草稿）的展示文案 */
const ARTICLE_STATUS_DRAFT_TEXT = "草稿";
/** 分类缺失时的展示文案 */
const UNCATEGORIZED_TEXT = "未分类";
/** 时间等字段缺失时的占位文案，避免三种格式出现空白行 */
const EMPTY_FIELD_TEXT = "—";

/**
 * 文章导出服务，负责拉取文章与作者信息并生成 Word、Markdown、PDF 文件上传到 OSS 返回下载链接
 */
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
    const { article, user } = await this.loadArticleWithAuthor(id);
    const meta: ArticleExportMeta = this.buildExportMeta(article, user);
    const htmlContent: string = marked.parse(article.content || "");
    const data: Record<string, unknown> = {
      id: meta.id,
      title: meta.title,
      author: meta.author,
      category: meta.category,
      status: meta.status,
      tags: ExportTemplate.formatTags(meta.tags),
      views: meta.views,
      createTime: meta.createTime,
      updateTime: meta.updateTime,
      content: htmlContent,
    };
    const wordDir: string = this.resolveWordDir(); // 模板目录，仅用于读取模板
    const templatePath: string = path.join(wordDir, "template.docx"); // 模板文件路径
    const savePath: string = path.join(
      await this.prepareExportDir(),
      `article-${id}.docx`,
    ); // 保存路径
    // 调用 WordService 生成并保存 Word 文档
    const buffer: Buffer = await this.wordService.exportToWord(
      data,
      templatePath,
    );
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

  // 准备导出中间目录，生成的文件上传后即删除，避免静态目录权限不足导致导出失败
  private async prepareExportDir(): Promise<string> {
    await fs.promises.mkdir(EXPORT_TEMP_DIR, { recursive: true });
    return EXPORT_TEMP_DIR;
  }

  // 解析 Word 目录：绝对路径直接使用，相对路径基于进程工作目录，避免容器内工作目录与配置不一致时拼出错误路径
  private resolveWordDir(): string {
    const filePath: string | undefined =
      this.configService.get<string>("files.word");
    if (!filePath) {
      throw BusinessException.notFound(
        Messages.EMPTY_FILE_PATH,
        ErrorIds.EMPTY_FILE_PATH,
      );
    }
    return path.isAbsolute(filePath)
      ? filePath
      : path.resolve(process.cwd(), filePath);
  }

  // 生成markdown文件并上传到OSS，返回下载链接
  async exportMarkdownAndUpload(id: number): Promise<string> {
    const { article, user } = await this.loadArticleWithAuthor(id);
    const meta: ArticleExportMeta = this.buildExportMeta(article, user);
    // Markdown 结构模板统一由 ExportTemplate 常量类提供
    const markdown: string = ExportTemplate.renderArticleMarkdown(
      meta,
      article.content || "",
    );
    // 保存到本地临时文件
    const saveDir: string = await this.prepareExportDir();
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
    const { article, user } = await this.loadArticleWithAuthor(id);
    const meta: ArticleExportMeta = this.buildExportMeta(article, user);

    // 获取文件保存路径
    const saveDir: string = await this.prepareExportDir();
    const savePath: string = path.join(saveDir, `article-${id}.pdf`);

    // 使用 marked 解析 Markdown 内容为 HTML，再套用 PDF 模板
    const htmlContent: string = ExportTemplate.renderArticleHtml(
      meta,
      marked.parse(article.content || ""),
    );

    // 使用 puppeteer 生成 PDF，容器内由镜像的 PUPPETEER_EXECUTABLE_PATH 指向系统 chromium
    const browser: Browser = await launch({
      headless: true,
      args: [
        "--no-sandbox",
        "--disable-setuid-sandbox",
        "--disable-dev-shm-usage",
      ],
    });

    try {
      const page: Page = await browser.newPage();
      try {
        await page.setContent(htmlContent, { waitUntil: "networkidle0" });
        await page.pdf({
          path: savePath,
          format: ExportTemplate.PAGE_SIZE,
          margin: {
            top: ExportTemplate.PAGE_MARGIN,
            bottom: ExportTemplate.PAGE_MARGIN,
            left: ExportTemplate.PAGE_MARGIN,
            right: ExportTemplate.PAGE_MARGIN,
          },
          printBackground: true,
          // 页脚注入页码，页眉不输出，避免与正文标题重复
          displayHeaderFooter: true,
          headerTemplate: "<span></span>",
          footerTemplate: ExportTemplate.PDF_FOOTER_TEMPLATE,
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

  /**
   * 拉取文章与作者信息，作者缺失（文章未关联用户）时返回 null
   * @param id 文章 ID
   */
  private async loadArticleWithAuthor(
    id: number,
  ): Promise<{ article: RemoteArticle; user: RemoteUser | null }> {
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

    // 文章未关联作者（user_id 为空）时跳过，避免调用 GET /users/null 触发 spring 路径变量类型转换 400
    if (article.user_id == null) {
      return { article, user: null };
    }
    const userRes: Record<string, unknown> =
      await this.springClient.getUserById(article.user_id);
    return {
      article,
      user: SpringClientService.extractData<RemoteUser | null>(userRes),
    };
  }

  /**
   * 构造三种导出格式共用的元信息，字段缺失时填充占位文案
   * @param article 远程文章数据
   * @param user 远程作者数据，缺失时回退为未知用户
   */
  private buildExportMeta(
    article: RemoteArticle,
    user: RemoteUser | null,
  ): ArticleExportMeta {
    const category: string = [article.category_name, article.sub_category_name]
      .filter((name: string | null): boolean => Boolean(name))
      .join(" / ");
    return {
      id: article.id,
      title: article.title || "",
      author: user?.name || Messages.UNKNOWN_USER,
      category: category || UNCATEGORIZED_TEXT,
      status:
        article.status === ARTICLE_STATUS_PUBLISHED
          ? ARTICLE_STATUS_PUBLISHED_TEXT
          : ARTICLE_STATUS_DRAFT_TEXT,
      tags: ExportTemplate.parseTags(article.tags),
      views: article.views ?? 0,
      createTime: this.formatTime(article.create_at),
      updateTime: this.formatTime(article.update_at),
    };
  }

  /**
   * 格式化远程时间字段，缺失时返回占位文案
   * @param value 远程时间字符串
   */
  private formatTime(value: string | null): string {
    return value
      ? dayjs(value).format("YYYY-MM-DD HH:mm:ss")
      : EMPTY_FIELD_TEXT;
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

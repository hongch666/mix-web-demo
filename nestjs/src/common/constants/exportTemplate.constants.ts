/**
 * 文章导出模板常量 — 文章转 PDF / Markdown 使用的结构与样式模板
 *
 * 说明：
 * - Word 模板为二进制 docx（`src/assets/word/template.docx`），占位符与 ArticleExportMeta 的字段一一对应
 * - PDF 的 HTML 模板对缩进不敏感，按常规缩进书写
 * - Markdown 对换行与缩进敏感，模板体顶格书写
 * - 三种格式共用 ArticleExportMeta，避免各写一套取值逻辑导致导出内容不一致
 */
import type { ArticleExportMeta } from "src/common/interfaces";

/**
 * HTML 转义映射，避免标题、作者、分类等外部文本破坏模板结构
 */
const HTML_ESCAPE_MAP: Record<string, string> = {
  "&": "&amp;",
  "<": "&lt;",
  ">": "&gt;",
  '"': "&quot;",
  "'": "&#39;",
};

/**
 * Markdown / YAML 双引号字符串转义映射
 */
const QUOTE_ESCAPE_MAP: Record<string, string> = {
  "\\": "\\\\",
  '"': '\\"',
};

export class ExportTemplate {
  // ===== PDF 模板 =====

  /**
   * 渲染文章 PDF 的完整 HTML
   * @param meta 导出元信息
   * @param content 正文 HTML（已由 marked 渲染，不再转义）
   */
  static readonly renderArticleHtml = (
    meta: ArticleExportMeta,
    content: string,
  ): string => `
      <!DOCTYPE html>
      <html lang="zh-CN">
      <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>${ExportTemplate.escapeHtml(meta.title)}</title>
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
            font-family: 'Noto Sans CJK SC', 'Source Han Sans SC', 'Microsoft YaHei', 'Segoe UI', 'SimSun', sans-serif;
            font-size: 14px;
            line-height: 1.9;
            color: #2b2b2b;
            background: white;
          }
          @page {
            size: A4;
          }
          .title {
            font-size: 26px;
            font-weight: 700;
            line-height: 1.4;
            text-align: center;
            color: #111;
            margin-bottom: 14px;
          }
          .meta {
            text-align: center;
            font-size: 12px;
            color: #666;
            margin-bottom: 6px;
          }
          .meta .dot {
            margin: 0 6px;
            color: #bbb;
          }
          .timeline {
            text-align: center;
            font-size: 11px;
            color: #8c8c8c;
            margin-bottom: 10px;
          }
          .tags {
            text-align: center;
            margin-bottom: 14px;
          }
          .tag {
            display: inline-block;
            font-size: 11px;
            color: #1f6feb;
            background: #eaf2ff;
            border: 1px solid #cfe1ff;
            border-radius: 10px;
            padding: 1px 9px;
            margin: 0 3px;
            line-height: 1.7;
          }
          .tag-empty {
            font-size: 11px;
            color: #a0a0a0;
          }
          .divider {
            border: none;
            border-top: 1px solid #d9d9d9;
            margin: 0 0 16px 0;
          }
          .content {
            font-size: 14px;
            line-height: 1.9;
            color: #2b2b2b;
          }
          .content h1 {
            font-size: 21px;
            font-weight: 700;
            margin: 18px 0 8px 0;
            color: #111;
            page-break-after: avoid;
          }
          .content h2 {
            font-size: 18px;
            font-weight: 700;
            margin: 16px 0 8px 0;
            color: #111;
            border-bottom: 1px solid #e6e6e6;
            padding-bottom: 4px;
            page-break-after: avoid;
          }
          .content h3 {
            font-size: 16px;
            font-weight: 700;
            margin: 14px 0 6px 0;
            page-break-after: avoid;
          }
          .content h4,
          .content h5,
          .content h6 {
            font-size: 14px;
            font-weight: 700;
            margin: 12px 0 6px 0;
            page-break-after: avoid;
          }
          .content p {
            margin: 8px 0;
            text-align: justify;
          }
          .content ul,
          .content ol {
            margin: 8px 0 8px 22px;
          }
          .content li {
            margin: 4px 0;
          }
          .content blockquote {
            border-left: 3px solid #d0d0d0;
            margin: 10px 0;
            padding: 2px 0 2px 14px;
            color: #666;
            font-size: 13px;
          }
          .content code {
            background-color: #f4f4f4;
            padding: 1px 5px;
            border-radius: 3px;
            font-family: 'Courier New', 'Consolas', monospace;
            font-size: 12px;
          }
          .content pre {
            background-color: #f8f8f8;
            border: 1px solid #e6e6e6;
            border-radius: 4px;
            padding: 10px 12px;
            overflow-x: auto;
            margin: 10px 0;
            line-height: 1.5;
            font-size: 11px;
            page-break-inside: avoid;
          }
          .content pre code {
            background-color: transparent;
            padding: 0;
            font-size: 11px;
          }
          .content table {
            border-collapse: collapse;
            margin: 10px 0;
            width: 100%;
            font-size: 12px;
            page-break-inside: avoid;
          }
          .content table th,
          .content table td {
            border: 1px solid #dcdcdc;
            padding: 5px 8px;
            text-align: left;
          }
          .content table th {
            background-color: #f5f5f5;
            font-weight: 700;
          }
          .content img {
            max-width: 100%;
          }
          .content hr {
            border: none;
            border-top: 1px solid #e6e6e6;
            margin: 14px 0;
          }
          .footer {
            margin-top: 28px;
            padding-top: 10px;
            border-top: 1px solid #e6e6e6;
            text-align: center;
            font-size: 10px;
            line-height: 1.8;
            color: #a0a0a0;
          }
          .footer .footer-id {
            font-size: 11px;
            color: #8c8c8c;
          }
        </style>
      </head>
      <body>
        <div class="title">${ExportTemplate.escapeHtml(meta.title)}</div>

        <div class="meta">
          <span>${ExportTemplate.escapeHtml(meta.author)}</span>
          <span class="dot">·</span>
          <span>${ExportTemplate.escapeHtml(meta.category)}</span>
          <span class="dot">·</span>
          <span>${ExportTemplate.escapeHtml(meta.status)}</span>
          <span class="dot">·</span>
          <span>阅读 ${meta.views}</span>
        </div>

        <div class="timeline">
          创作于 ${ExportTemplate.escapeHtml(meta.createTime)} | 更新于 ${ExportTemplate.escapeHtml(meta.updateTime)}
        </div>

        <div class="tags">${ExportTemplate.renderHtmlTags(meta.tags)}</div>

        <hr class="divider">

        <div class="content">${content}</div>

        <div class="footer">
          <div class="footer-id">文章编号 #${meta.id}</div>
          <div>本文件由${ExportTemplate.PLATFORM_NAME}自动生成</div>
        </div>
      </body>
      </html>
    `;

  // ===== Markdown 模板 =====

  /**
   * 渲染文章导出的完整 Markdown 内容
   * @param meta 导出元信息
   * @param content 正文 Markdown
   */
  static readonly renderArticleMarkdown = (
    meta: ArticleExportMeta,
    content: string,
  ): string => `---
title: "${ExportTemplate.escapeYaml(meta.title)}"
article_id: ${meta.id}
author: "${ExportTemplate.escapeYaml(meta.author)}"
category: "${ExportTemplate.escapeYaml(meta.category)}"
status: "${ExportTemplate.escapeYaml(meta.status)}"
tags: ${ExportTemplate.renderYamlTags(meta.tags)}
views: ${meta.views}
created_at: "${ExportTemplate.escapeYaml(meta.createTime)}"
updated_at: "${ExportTemplate.escapeYaml(meta.updateTime)}"
---

# ${meta.title}

> ${meta.author} · ${meta.category} · ${meta.status} · 阅读 ${meta.views}
>
> 创作于 ${meta.createTime} | 更新于 ${meta.updateTime}

**标签：** ${ExportTemplate.renderMarkdownTags(meta.tags)}

---

${content}

---

<sub>文章编号 #${meta.id} · 本文件由${ExportTemplate.PLATFORM_NAME}自动生成</sub>
`;

  // ===== 字段格式化 =====

  /**
   * 将标签列表拼接为单行文本，供 docx 模板的 ${tags} 占位符使用
   * @param tags 标签列表
   */
  static readonly formatTags = (tags: string[]): string =>
    tags.length ? tags.join("、") : ExportTemplate.EMPTY_TAGS;

  /**
   * 拆分标签字符串，兼容中英文逗号与分号，并去除空项
   * @param tags 原始标签字符串，如 "Java,分布式"
   */
  static readonly parseTags = (tags: string | null | undefined): string[] =>
    (tags || "")
      .split(/[,，;；]/)
      .map((tag: string): string => tag.trim())
      .filter((tag: string): boolean => tag.length > 0);

  // ===== 内部渲染辅助 =====

  /**
   * 渲染 HTML 标签块，为空时输出占位文案
   * @param tags 标签列表
   */
  private static readonly renderHtmlTags = (tags: string[]): string =>
    tags.length
      ? tags
          .map(
            (tag: string): string =>
              `<span class="tag">${ExportTemplate.escapeHtml(tag)}</span>`,
          )
          .join("")
      : `<span class="tag-empty">${ExportTemplate.EMPTY_TAGS}</span>`;

  /**
   * 渲染 Markdown 行内标签，为空时输出占位文案
   * @param tags 标签列表
   */
  private static readonly renderMarkdownTags = (tags: string[]): string =>
    tags.length
      ? tags.map((tag: string): string => `\`${tag}\``).join(" ")
      : ExportTemplate.EMPTY_TAGS;

  /**
   * 渲染 Markdown front matter 的标签数组
   * @param tags 标签列表
   */
  private static readonly renderYamlTags = (tags: string[]): string =>
    tags.length
      ? `\n${tags
          .map(
            (tag: string): string => `  - "${ExportTemplate.escapeYaml(tag)}"`,
          )
          .join("\n")}`
      : " []";

  /**
   * 转义 HTML 特殊字符，避免外部文本破坏模板结构
   * @param value 原始文本
   */
  private static readonly escapeHtml = (value: string): string =>
    (value || "").replace(
      /[&<>"']/g,
      (char: string): string => HTML_ESCAPE_MAP[char] ?? char,
    );

  /**
   * 转义 YAML 双引号字符串中的反斜杠与双引号
   * @param value 原始文本
   */
  private static readonly escapeYaml = (value: string): string =>
    (value || "").replace(
      /[\\"]/g,
      (char: string): string => QUOTE_ESCAPE_MAP[char] ?? char,
    );

  // ===== 文案与版式 =====

  /** 导出文件的来源平台名，写入三种格式的页脚 */
  static readonly PLATFORM_NAME = "多语言微服务智能文章平台";

  /** 标签为空时的展示文案 */
  static readonly EMPTY_TAGS = "无标签";

  /** 导出 PDF 使用的纸张规格 */
  static readonly PAGE_SIZE = "A4";

  /** 导出 PDF 使用的页边距 */
  static readonly PAGE_MARGIN = "15mm";

  /** 导出 PDF 页脚模板，注入 puppeteer 显示页码 */
  static readonly PDF_FOOTER_TEMPLATE: string = `
    <div style="width:100%;font-size:9px;color:#999;text-align:center;font-family:'Noto Sans CJK SC','Microsoft YaHei',sans-serif;">
      第 <span class="pageNumber"></span> / <span class="totalPages"></span> 页
    </div>
  `;
}

/**
 * PDF 导出模板常量 — 文章转 PDF 使用的页面样式与结构模板
 */
export class PdfTemplate {
  // ===== 页面设置 =====
  static readonly PAGE_SIZE = "A4";
  static readonly PAGE_MARGIN = "15mm";

  /**
   * 渲染文章 PDF 的完整 HTML
   * @param title 文章标题
   * @param username 作者名
   * @param createTime 创作时间
   * @param tags 标签（为空时不渲染标签区块）
   * @param content 正文 HTML
   */
  static readonly renderArticleHtml = (
    title: string,
    username: string,
    createTime: string,
    tags: string,
    content: string,
  ): string => `
      <!DOCTYPE html>
      <html lang="zh-CN">
      <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>${title}</title>
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
          <div class="title">${title}</div>

          <div class="meta-info">
            <div>作者: ${username}</div>
            <div>创作时间: ${createTime}</div>
          </div>

          ${tags ? `<div class="tags">标签: ${tags}</div>` : ""}

          <div class="divider"></div>

          <div class="content">${content}</div>

        </div>
      </body>
      </html>
    `;
}

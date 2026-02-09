declare module 'html-to-text' {
  export interface HtmlToTextOptions {
    wordwrap?: number | boolean | null;
    tables?: boolean | any[];
    ignoreHref?: boolean;
    ignoreImage?: boolean;
    preserveNewlines?: boolean;
    uppercaseHeadings?: boolean;
    singleNewLineParagraphs?: boolean;
    baseElements?: {
      selectors?: string[];
      returnDomByDefault?: boolean;
    };
    selectors?: Array<{
      selector: string;
      options?: HtmlToTextOptions;
    }>;
  }

  export function htmlToText(html: string, options?: HtmlToTextOptions): string;
  export { htmlToText as convert };
}

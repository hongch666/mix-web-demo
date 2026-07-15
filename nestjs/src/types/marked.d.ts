declare module "marked" {
  export interface MarkedOptions {
    breaks?: boolean;
    gfm?: boolean;
    headerIds?: boolean;
    headerPrefix?: string;
    highlight?: (code: string, lang?: string) => string;
    langPrefix?: string;
    mangle?: boolean;
    pedantic?: boolean;
    renderer?: unknown;
    sanitize?: boolean;
    sanitizer?: (html: string) => string;
    silent?: boolean;
    smartLists?: boolean;
    smartypants?: boolean;
    tokenizer?: unknown;
    walkTokens?: (token: unknown) => void;
  }

  export function parse(markdown: string, options?: MarkedOptions): string;
  export function parseInline(
    markdown: string,
    options?: MarkedOptions,
  ): string;
  export function setOptions(options: MarkedOptions): void;

  const marked: {
    parse: typeof parse;
    parseInline: typeof parseInline;
    setOptions: typeof setOptions;
  };

  export = marked;
}

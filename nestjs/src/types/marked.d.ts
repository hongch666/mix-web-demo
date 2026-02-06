declare module 'marked' {
  export interface MarkedOptions {
    breaks?: boolean;
    gfm?: boolean;
    headerIds?: boolean;
    headerPrefix?: string;
    highlight?: (code: string, lang?: string) => string;
    langPrefix?: string;
    mangle?: boolean;
    pedantic?: boolean;
    renderer?: any;
    sanitize?: boolean;
    sanitizer?: (html: string) => string;
    silent?: boolean;
    smartLists?: boolean;
    smartypants?: boolean;
    tokenizer?: any;
    walkTokens?: (token: any) => void;
  }

  export function parse(markdown: string, options?: MarkedOptions): string;
  export function parseInline(markdown: string, options?: MarkedOptions): string;
  export function setOptions(options: MarkedOptions): void;

  const marked: {
    parse: typeof parse;
    parseInline: typeof parseInline;
    setOptions: typeof setOptions;
  };

  export = marked;
}
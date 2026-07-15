declare module "puppeteer" {
  interface LaunchOptions {
    headless?: boolean | "new";
    args?: string[];
    executablePath?: string;
    timeout?: number;
    [key: string]: unknown;
  }

  interface PDFOptions {
    path?: string;
    format?: string;
    margin?: {
      top?: string;
      bottom?: string;
      left?: string;
      right?: string;
    };
    printBackground?: boolean;
    [key: string]: unknown;
  }

  interface SetContentOptions {
    waitUntil?: string | string[];
  }

  interface Page {
    setContent(html: string, options?: SetContentOptions): Promise<void>;
    pdf(options?: PDFOptions): Promise<Buffer>;
    close(): Promise<void>;
  }

  interface Browser {
    newPage(): Promise<Page>;
    close(): Promise<void>;
  }

  export function launch(options?: LaunchOptions): Promise<Browser>;
  export { Browser, Page };
}

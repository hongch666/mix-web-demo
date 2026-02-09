declare module 'docx-templates' {
  export interface CreateReportOptions {
    template: Buffer;
    data: Record<string, any>;
    cmdDelimiter?: [string, string];
    additionalJsContext?: Record<string, any>;
    processLineBreaks?: boolean;
    noSandbox?: boolean;
  }

  export interface CreateReportResult {
    [Symbol.asyncIterator](): AsyncIterableIterator<Buffer>;
  }

  export function createReport(options: CreateReportOptions): Promise<Buffer>;
}

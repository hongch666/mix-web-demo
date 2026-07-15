declare module "docx-templates" {
  export interface CreateReportOptions {
    template: Buffer;
    data: Record<string, unknown>;
    cmdDelimiter?: [string, string];
    additionalJsContext?: Record<string, unknown>;
    processLineBreaks?: boolean;
    noSandbox?: boolean;
  }

  export interface CreateReportResult {
    [Symbol.asyncIterator](): AsyncIterableIterator<Buffer>;
  }

  export function createReport(options: CreateReportOptions): Promise<Buffer>;
}

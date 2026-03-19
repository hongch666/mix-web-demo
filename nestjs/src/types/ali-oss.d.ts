declare module 'ali-oss' {
  export interface OSSOptions {
    accessKeyId: string;
    accessKeySecret: string;
    bucket: string;
    endpoint: string;
    secure?: boolean;
    [key: string]: unknown;
  }

  export interface PutResult {
    name: string;
    url: string;
    res: any;
  }

  export default class OSS {
    constructor(options: OSSOptions);
    put(name: string, file: string): Promise<PutResult>;
  }
}

// module/common/oss 目录的公开出口，跨目录引用统一从此处导入
export { OssModule } from "./oss.module";
export { detectOssRuntime } from "./oss.service";
export { OssService } from "./oss.service";
export type { OssObjectInfo } from "./oss.service";
export type { OssListPage } from "./oss.service";
export type { OssListOptions } from "./oss.service";
export type { OssListRawResult } from "./oss.service";
export type { OssClient } from "./oss.service";
export { OSS_CLIENT } from "./oss.tokens";
export { OSS_RUNTIME } from "./oss.tokens";
export type { OssRuntime } from "./oss.tokens";

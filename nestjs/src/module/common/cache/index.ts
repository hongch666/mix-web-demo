// module/common/cache 目录的公开出口，跨目录引用统一从此处导入
export { CacheModule } from "./cache.module";
export { CacheService } from "./cache.service";
export type { CacheWriteOptions } from "src/framework/explorer";

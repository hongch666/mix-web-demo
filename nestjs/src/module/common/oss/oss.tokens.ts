/** ali-oss 客户端注入令牌 */
export const OSS_CLIENT = Symbol("OSS_CLIENT");

/** OSS 运行时策略注入令牌 */
export const OSS_RUNTIME = Symbol("OSS_RUNTIME");

/** OSS 文件操作使用的底层实现 */
export type OssRuntime = "ali-oss" | "bun";

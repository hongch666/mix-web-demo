// 全局类型声明：为缺少 @types 包的依赖补充类型定义
/// <reference path="./aliOss.d.ts" />
/// <reference path="./fastifyMultipart.d.ts" />
/// <reference path="./nacos.d.ts" />
/// <reference path="./puppeteer.d.ts" />
/// <reference path="./htmlToText.d.ts" />
/// <reference path="./docxTemplates.d.ts" />
/// <reference path="./marked.d.ts" />
/// <reference path="./qs.d.ts" />

// 统一再导出，便于按包名引用
export * from "./aliOss";
export * from "./docxTemplates";
export * from "./fastifyMultipart";
export * from "./htmlToText";
export * from "./marked";
export * from "./nacos";
export * from "./puppeteer";
export * from "./qs";

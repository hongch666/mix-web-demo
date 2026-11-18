import * as fs from "fs";
import * as path from "path";
import JavaScriptObfuscator, {
  type ObfuscatorOptions,
} from "javascript-obfuscator";

const DIST_DIR: string = path.join(__dirname, "..");

/** 混淆选项：保留 NestJS 依赖注入所需类名与导出接口，抹除方法名、字段名与字符串常量 */
const OPTIONS: ObfuscatorOptions = {
  compact: true,
  controlFlowFlattening: false,
  deadCodeInjection: false,
  stringArray: true,
  stringArrayEncoding: ["base64"],
  stringArrayThreshold: 0.75,
  identifierNamesGenerator: "hexadecimal",
  transformObjectKeys: false,
  selfDefending: false,
  target: "node",
};

/** 遍历构建目录混淆业务脚本，跳过 script 目录避免处理构建工具本身 */
function obfuscateDirectory(dir: string): void {
  for (const name of fs.readdirSync(dir)) {
    const full: string = path.join(dir, name);
    if (fs.statSync(full).isDirectory()) {
      if (name === "script") continue;
      obfuscateDirectory(full);
      continue;
    }
    if (!name.endsWith(".js")) continue;

    const source: string = fs.readFileSync(full, "utf8");
    const result = JavaScriptObfuscator.obfuscate(source, OPTIONS);
    fs.writeFileSync(full, result.getObfuscatedCode());
  }
}

/** 递归删除构建产物中的类型声明与 sourcemap，避免镜像暴露源码结构 */
function cleanExtraFiles(dir: string): void {
  for (const name of fs.readdirSync(dir)) {
    const full: string = path.join(dir, name);
    if (fs.statSync(full).isDirectory()) {
      cleanExtraFiles(full);
      continue;
    }
    if (name.endsWith(".d.ts") || name.endsWith(".js.map")) {
      fs.rmSync(full);
    }
  }
}

obfuscateDirectory(DIST_DIR);
cleanExtraFiles(DIST_DIR);
console.log("源码混淆与构建产物清理完成");

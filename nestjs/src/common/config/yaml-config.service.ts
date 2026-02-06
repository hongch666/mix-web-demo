import * as yaml from 'js-yaml';
import * as fs from 'fs';
import { config } from 'dotenv';

// 加载 .env 文件
config();

/**
 * 递归解析YAML中的环境变量占位符
 * 支持格式：${VAR_NAME:default_value} 或 ${VAR_NAME}
 */
function resolveEnvVars(obj: any): any {
  if (typeof obj === 'string') {
    // 匹配 ${VAR_NAME:default_value} 或 ${VAR_NAME}
    return obj.replace(/\$\{([^:}]+)(?::([^}]*))?\}/g, (_: string, key: string, defaultVal?: string): string => {
      const value: string | undefined = process.env[key];
      if (value !== undefined) {
        return value;
      }
      return defaultVal !== undefined ? defaultVal : '';
    });
  }
  if (Array.isArray(obj)) {
    return obj.map((item: any) => resolveEnvVars(item));
  }
  if (obj !== null && typeof obj === 'object') {
    return Object.entries(obj).reduce(
      (acc: Record<string, any>, [key, val]: [string, any]) => {
        acc[key] = resolveEnvVars(val);
        return acc;
      },
      {} as Record<string, any>,
    );
  }
  return obj;
}

export default (): Record<string, any> => {
  const YAML_CONFIG_FILENAME: string = 'application.yaml'; // 项目根目录路径
  const fileContents: string = fs.readFileSync(YAML_CONFIG_FILENAME, 'utf8');
  let configObj: Record<string, any> = yaml.load(fileContents) as Record<string, any>;

  // 递归替换环境变量
  configObj = resolveEnvVars(configObj);

  return configObj;
};

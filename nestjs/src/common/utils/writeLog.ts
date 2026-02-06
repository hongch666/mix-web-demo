import { Logger } from '@nestjs/common';
import * as fs from 'fs';
import * as path from 'path';
import yamlConfig from '../config/yaml-config.service';
import { BusinessException } from '../exceptions/business.exception';

export class LoggerUtil {
  private static logPath: string;
  private static configLoaded: boolean = false;

  // 静态初始化配置
  private static loadConfig(): void {
    if (this.configLoaded) return;

    try {
      // 复用现有的 YAML 配置服务
      const config: Record<string, any> = yamlConfig();

      // 获取日志路径，支持环境变量覆盖
      this.logPath = process.env.LOG_PATH || config?.logs?.path || 'logs';
      this.configLoaded = true;
      Logger.log(`日志配置加载成功，路径: ${this.logPath}`);
    } catch (error: any) {
      throw new BusinessException(`加载日志配置失败: ${error.message}`);
    }
  }

  /**
   * 直接写入日志到文件
   * @param message 日志消息
   * @param level 日志级别
   */
  static writeLog(message: string, level: string = 'INFO'): void {
    // 确保配置已加载
    this.loadConfig();

    // 确保日志目录存在
    if (!fs.existsSync(this.logPath)) {
      fs.mkdirSync(this.logPath, { recursive: true });
    }

    // 日志文件名 (按日期)
    const today: string = new Date().toISOString().split('T')[0];
    const logFile: string = path.join(this.logPath, `app_${today}.log`);

    // 格式化日志消息
    const timestamp: string = new Date()
      .toISOString()
      .replace('T', ' ')
      .substring(0, 19);
    const logEntry: string = `${timestamp} - ${level} - ${message}\n`;

    // 写入文件
    try {
      fs.appendFileSync(logFile, logEntry, 'utf8');
    } catch (error: any) {
      throw new BusinessException(`写入日志失败: ${error.message}`);
    }
  }

  // 便捷静态方法
  static logInfo(message: string): void {
    Logger.log(message);
    this.writeLog(message, 'INFO');
  }

  static logError(message: string): void {
    Logger.error(message);
    this.writeLog(message, 'ERROR');
  }

  static logWarning(message: string): void {
    Logger.warn(message);
    this.writeLog(message, 'WARNING');
  }

  static logDebug(message: string): void {
    Logger.debug(message);
    this.writeLog(message, 'DEBUG');
  }

  // 获取当前日志路径
  static getLogPath(): string {
    this.loadConfig();
    return this.logPath;
  }

  // 手动重新加载配置
  static reloadConfig(): void {
    this.configLoaded = false;
    this.loadConfig();
  }
}

// SimpleLogger 类
export class SimpleLogger {
  info(message: string): void {
    LoggerUtil.logInfo(message);
  }

  error(message: string): void {
    LoggerUtil.logError(message);
  }

  warning(message: string): void {
    LoggerUtil.logWarning(message);
  }

  debug(message: string): void {
    LoggerUtil.logDebug(message);
  }
}

// 导出静态方法和实例
export const { logInfo, logError, logWarning, logDebug, writeLog } = LoggerUtil;
export const logger = new SimpleLogger();

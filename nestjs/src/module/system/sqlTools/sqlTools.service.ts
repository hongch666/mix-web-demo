import { Injectable } from "@nestjs/common";
import { InjectDataSource } from "@nestjs/typeorm";
import { ErrorIds, HttpCode, Messages, SqlTools } from "src/common/constants";
import { BusinessException } from "src/common/exceptions/business.exception";
import { DataSource } from "typeorm";

const TABLE_WHITELIST = new Set<string>(SqlTools.TABLE_WHITELIST);
const ALLOWED_PREFIXES = SqlTools.ALLOWED_PREFIXES;
const TABLE_NAME_REGEX = SqlTools.TABLE_NAME_REGEX;
const LIMIT_REGEX = SqlTools.LIMIT_REGEX;
const NAMED_PARAM_REGEX = SqlTools.NAMED_PARAM_REGEX;
const MAX_LIMIT = SqlTools.MAX_LIMIT;

interface TableInfo {
  table: string;
  rowCount?: number;
  columns?: unknown[];
}

/**
 * SQL工具服务，提供受限的只读参数化SQL查询能力
 * 仅允许查询白名单内的表，且强制参数化占位符和 LIMIT
 */
@Injectable()
export class SqlToolsService {
  constructor(@InjectDataSource() private readonly dataSource: DataSource) {}

  /**
   * 获取表结构信息
   * @param table 表名，为空则返回所有白名单表
   */
  async getTables(table?: string): Promise<unknown> {
    if (table) {
      return this.getSingleTableSchema(table.trim());
    }
    return this.getAllTableSchemas();
  }

  /**
   * 执行只读参数化SQL查询
   * @param query 参数化SQL（使用 :paramName 占位符）
   * @param params 参数键值对
   */
  async executeQuery(
    query: string,
    params: Record<string, unknown>,
  ): Promise<unknown> {
    const validatedQuery = this.validateQuery(query);

    try {
      // 将命名参数 :paramName 替换为 ? 占位符，values 按顺序对应
      const { query: replacedQuery, values } = this.replaceNamedParams(
        validatedQuery,
        params,
      );
      const rows = await this.dataSource.query(replacedQuery, values);
      if (!Array.isArray(rows) || rows.length === 0) {
        return { columns: [], rows: [], rowCount: 0 };
      }

      const columns = Object.keys(rows[0]);
      const rowValues = rows.map((row: Record<string, unknown>) =>
        columns.map((col) => row[col]),
      );
      return { columns, rows: rowValues, rowCount: rows.length };
    } catch (e) {
      throw new BusinessException(
        Messages.SQL_PROXY_QUERY_FAILED((e as Error).message),
        HttpCode.INTERNAL_SERVER_ERROR,
        ErrorIds.NESTJS_SERVER_ERROR,
      );
    }
  }

  /**
   * 校验SQL语句安全性
   */
  private validateQuery(query: string): string {
    if (!query || query.trim().length === 0) {
      throw new BusinessException(
        Messages.SQL_PROXY_QUERY_NOT_EMPTY,
        HttpCode.BAD_REQUEST,
        ErrorIds.PARAM_PARSE_FAILED,
      );
    }

    let normalized = query.trim().replace(/\s+/g, " ");
    const upperNormalized = () => normalized.toUpperCase();

    // 1. 检查多条语句
    if (normalized.includes(";")) {
      const withoutTrailing = normalized.replace(/;\s*$/, "");
      if (withoutTrailing.includes(";")) {
        throw new BusinessException(
          Messages.SQL_PROXY_MULTIPLE_STATEMENTS,
          HttpCode.BAD_REQUEST,
          ErrorIds.PARAM_PARSE_FAILED,
        );
      }
      normalized = withoutTrailing;
    }

    // 2. 检查语句类型
    const allowed = ALLOWED_PREFIXES.some((prefix) =>
      upperNormalized().startsWith(prefix),
    );
    if (!allowed) {
      throw new BusinessException(
        Messages.SQL_PROXY_FORBIDDEN_STATEMENT,
        HttpCode.BAD_REQUEST,
        ErrorIds.PARAM_PARSE_FAILED,
      );
    }

    // 3. 检查表名白名单
    TABLE_NAME_REGEX.lastIndex = 0;
    let match: RegExpExecArray | null;
    while ((match = TABLE_NAME_REGEX.exec(normalized)) !== null) {
      const tableName = match[1]!.toLowerCase();
      if (!TABLE_WHITELIST.has(tableName)) {
        throw new BusinessException(
          Messages.SQL_PROXY_TABLE_NOT_ALLOWED(tableName),
          HttpCode.BAD_REQUEST,
          ErrorIds.PARAM_PARSE_FAILED,
        );
      }
    }

    // 4. 检查 LIMIT
    const limitMatch = normalized.match(LIMIT_REGEX);
    if (!limitMatch) {
      throw new BusinessException(
        Messages.SQL_PROXY_LIMIT_REQUIRED,
        HttpCode.BAD_REQUEST,
        ErrorIds.PARAM_PARSE_FAILED,
      );
    }
    const limit = parseInt(limitMatch[1]!, 10);
    if (limit > MAX_LIMIT) {
      throw new BusinessException(
        Messages.SQL_PROXY_LIMIT_EXCEEDED,
        HttpCode.BAD_REQUEST,
        ErrorIds.PARAM_PARSE_FAILED,
      );
    }

    // 5. 检查参数化占位符
    if (!normalized.includes(":")) {
      throw new BusinessException(
        Messages.SQL_PROXY_PARAM_REQUIRED,
        HttpCode.BAD_REQUEST,
        ErrorIds.PARAM_PARSE_FAILED,
      );
    }

    return normalized;
  }

  /**
   * 将命名参数 :paramName 替换为 ? 占位符，返回新查询和对应的值数组
   */
  private replaceNamedParams(
    query: string,
    params: Record<string, unknown>,
  ): { query: string; values: unknown[] } {
    const values: unknown[] = [];
    const pattern = NAMED_PARAM_REGEX;
    const replaced = query.replace(pattern, (_, name) => {
      values.push(params[name]);
      return "?";
    });
    return { query: replaced, values };
  }

  /**
   * 获取单个表结构
   */
  private async getSingleTableSchema(tableName: string): Promise<unknown> {
    if (!TABLE_WHITELIST.has(tableName)) {
      throw new BusinessException(
        Messages.SQL_PROXY_TABLE_NOT_ALLOWED(tableName),
        HttpCode.BAD_REQUEST,
        ErrorIds.PARAM_PARSE_FAILED,
      );
    }

    try {
      const columns = await this.dataSource.query(
        "SHOW COLUMNS FROM `user_table_settings`",
      );
      const columnList = columns.map((col: Record<string, unknown>) => ({
        name: col.Field,
        type: col.Type,
        key: col.Key,
        comment: col.Comment ?? "",
      }));
      return { table: tableName, columns: columnList };
    } catch (e) {
      throw new BusinessException(
        Messages.SQL_PROXY_TABLE_SCHEMA_FAILED((e as Error).message),
        HttpCode.INTERNAL_SERVER_ERROR,
        ErrorIds.NESTJS_SERVER_ERROR,
      );
    }
  }

  /**
   * 获取所有白名单表
   */
  private async getAllTableSchemas(): Promise<TableInfo[]> {
    return [{ table: "user_table_settings" }];
  }
}

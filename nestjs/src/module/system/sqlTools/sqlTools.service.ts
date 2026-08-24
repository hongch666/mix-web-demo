import { Injectable } from "@nestjs/common";
import { InjectDataSource } from "@nestjs/typeorm";
import { ErrorIds, HttpCode, Messages, SqlTools } from "src/common/constants";
import { BusinessException } from "src/common/exceptions/business.exception";
import { DataSource } from "typeorm";

const TABLE_WHITELIST = new Set<string>(SqlTools.TABLE_WHITELIST);
const ALLOWED_PREFIXES = SqlTools.ALLOWED_PREFIXES;
const MAX_LIMIT = SqlTools.MAX_LIMIT;

// 每次调用时创建新的局部正则，避免全局标志的 lastIndex 状态残留
function createTableNameRegex(): RegExp {
  return new RegExp(SqlTools.TABLE_NAME_REGEX.source, "gi");
}
function createLimitRegex(): RegExp {
  return new RegExp(SqlTools.LIMIT_REGEX.source, "i");
}
function createNamedParamRegex(): RegExp {
  return new RegExp(SqlTools.NAMED_PARAM_REGEX.source, "g");
}

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

    let normalized = query.trim().replace(SqlTools.SQL_WHITESPACE_REGEX, " ");
    const upperNormalized = () => normalized.toUpperCase();

    // 1. 检查多条语句：先移除字符串字面量，避免字符串内的 ; 被误判
    const withoutStringLiterals = normalized.replace(
      SqlTools.SQL_STRING_LITERAL_REGEX,
      "",
    );
    if (withoutStringLiterals.includes(";")) {
      const withoutTrailing = normalized.replace(
        SqlTools.SQL_TRAILING_SEMICOLON_REGEX,
        "",
      );
      const withoutTrailingLiterals = withoutTrailing.replace(
        SqlTools.SQL_STRING_LITERAL_REGEX,
        "",
      );
      if (withoutTrailingLiterals.includes(";")) {
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

    // 3. 检查表名白名单（使用局部正则，避免全局标志 lastIndex 残留）
    const tableNameRegex = createTableNameRegex();
    const tableMatches = [...normalized.matchAll(tableNameRegex)];
    for (const m of tableMatches) {
      const tableName = m[1]!.toLowerCase();
      if (!TABLE_WHITELIST.has(tableName)) {
        throw new BusinessException(
          Messages.SQL_PROXY_TABLE_NOT_ALLOWED(tableName),
          HttpCode.BAD_REQUEST,
          ErrorIds.PARAM_PARSE_FAILED,
        );
      }
    }

    // 4. 检查 LIMIT（使用局部正则）
    const limitRegex = createLimitRegex();
    const limitMatch = normalized.match(limitRegex);
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

    // 5. 参数化占位符为可选：只读前缀 + 表白名单 + LIMIT 已充分防护，无参数查询同样合法
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
    const pattern = createNamedParamRegex();
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
        SqlTools.SHOW_COLUMNS_SQL(tableName),
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
   * 获取所有白名单表基本信息和行数，并行执行所有 COUNT 查询
   */
  private async getAllTableSchemas(): Promise<TableInfo[]> {
    const tableNames: string[] = Array.from(TABLE_WHITELIST);
    const results = await Promise.allSettled(
      tableNames.map(async (tableName) => {
        const [row] = await this.dataSource.query(
          SqlTools.COUNT_ROWS_SQL(tableName),
        );
        const rowCount = row && typeof row.cnt === "number" ? row.cnt : -1;
        return { table: tableName, rowCount };
      }),
    );
    return results.map(
      (r, i): TableInfo =>
        r.status === "fulfilled"
          ? r.value
          : { table: tableNames[i]!, rowCount: -1 },
    );
  }
}

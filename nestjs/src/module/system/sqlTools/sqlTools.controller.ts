import {
  Body,
  Controller,
  Get,
  HttpCode as HttpCodeDecorator,
  Post,
  Query,
} from "@nestjs/common";
import { ApiOperation, ApiQuery, ApiTags } from "@nestjs/swagger";
import { HttpCode } from "src/common/constants";
import {
  ApiResponseModel,
  SwaggerSqlQueryData,
  SwaggerSqlTablesData,
  success,
} from "src/common/utils";
import { ApiLog, RequireInternalToken } from "src/framework/decorators";
import { SqlQueryDto } from "./dto/sqlQuery.dto";
import { SqlToolsService } from "./sqlTools.service";

/**
 * SQL 工具接口，提供白名单表结构查询与只读参数化 SQL 执行，供内部服务远程调用
 */
@ApiTags("SQL工具")
@Controller("sql-tools")
export class SqlToolsController {
  constructor(private readonly sqlToolsService: SqlToolsService) {}

  /**
   * 查询白名单内 MySQL 表结构信息，不传表名时返回所有白名单表列表
   */
  @Get("tables")
  @ApiOperation({
    summary: "获取表结构信息",
    description:
      "查询白名单内 MySQL 表的结构信息，不传表名时返回所有白名单表列表，供内部服务远程调用",
  })
  @ApiQuery({
    name: "table",
    required: false,
    description: "表名，为空则返回所有白名单表",
  })
  @RequireInternalToken()
  @ApiLog({ message: "获取SQL工具表结构信息", skipMq: true })
  @ApiResponseModel({ data: SwaggerSqlTablesData })
  async getTables(@Query("table") table?: string) {
    const data = await this.sqlToolsService.getTables(table);
    return success(data);
  }

  /**
   * 在白名单表范围内执行参数化只读 SQL 查询并返回列与行数据
   */
  @Post("query")
  @HttpCodeDecorator(HttpCode.OK)
  @ApiOperation({
    summary: "执行只读参数化SQL",
    description:
      "在白名单表范围内执行参数化只读 SQL 查询并返回结果，供内部服务远程调用",
  })
  @RequireInternalToken()
  @ApiLog({ message: "执行SQL工具只读查询", skipMq: true })
  @ApiResponseModel({ data: SwaggerSqlQueryData })
  async executeQuery(@Body() dto: SqlQueryDto) {
    const data = await this.sqlToolsService.executeQuery(
      dto.query,
      dto.params ?? {},
    );
    return success(data);
  }
}

import { Body, Controller, Get, Post, Query } from "@nestjs/common";
import { ApiOperation, ApiQuery, ApiTags } from "@nestjs/swagger";
import { success } from "src/common/utils/response";
import { ApiLog } from "src/framework/decorators/apiLog.decorator";
import { RequireInternalToken } from "src/framework/decorators/requireInternalToken.decorator";
import { SqlQueryDto } from "./dto/sqlQuery.dto";
import { SqlToolsService } from "./sqlTools.service";

@ApiTags("SQL工具")
@Controller("sql-tools")
export class SqlToolsController {
  constructor(private readonly sqlToolsService: SqlToolsService) {}

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
  @ApiLog("获取SQL工具表结构信息")
  async getTables(@Query("table") table?: string) {
    const data = await this.sqlToolsService.getTables(table);
    return success(data);
  }

  @Post("query")
  @ApiOperation({
    summary: "执行只读参数化SQL",
    description:
      "在白名单表范围内执行参数化只读 SQL 查询并返回结果，供内部服务远程调用",
  })
  @RequireInternalToken()
  @ApiLog("执行SQL工具只读查询")
  async executeQuery(@Body() dto: SqlQueryDto) {
    const data = await this.sqlToolsService.executeQuery(
      dto.query,
      dto.params ?? {},
    );
    return success(data);
  }
}

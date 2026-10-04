package com.hcsy.spring.entity.vo;

import java.util.List;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 数据库表结构视图对象
 * 用于 SQL 代理工具返回白名单表信息
 */
@Data
@AllArgsConstructor
@NoArgsConstructor
@Schema(description = "数据库表结构")
public class SqlTableSchemaVO {

    @Schema(description = "表名")
    private String table;

    @Schema(description = "表行数，无法统计时为 -1，未查询时为空")
    private Integer rowCount;

    @Schema(description = "列信息，仅在指定表名查询时返回")
    private List<SqlColumnInfoVO> columns;
}

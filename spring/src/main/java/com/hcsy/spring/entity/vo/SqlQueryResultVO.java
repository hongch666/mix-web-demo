package com.hcsy.spring.entity.vo;

import java.util.List;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 只读 SQL 查询结果视图对象
 * 列与行结构由查询语句决定，行内值按列顺序排列
 */
@Data
@AllArgsConstructor
@NoArgsConstructor
@Schema(description = "只读SQL查询结果")
public class SqlQueryResultVO {

    @Schema(description = "结果列名，顺序与每行值的顺序一致")
    private List<String> columns;

    @Schema(description = "结果行，每行按列顺序排列")
    private List<List<Object>> rows;

    @Schema(description = "返回行数")
    private Integer rowCount;
}

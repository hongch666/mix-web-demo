package com.hcsy.spring.entity.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 数据库列信息视图对象
 * 用于 SQL 代理工具返回表结构
 */
@Data
@AllArgsConstructor
@NoArgsConstructor
@Schema(description = "数据库列信息")
public class SqlColumnInfoVO {

    @Schema(description = "列名")
    private String name;

    @Schema(description = "列类型")
    private String type;

    @Schema(description = "键类型，如 PRI")
    private String key;

    @Schema(description = "列注释")
    private String comment;
}

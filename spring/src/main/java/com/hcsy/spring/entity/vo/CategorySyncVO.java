package com.hcsy.spring.entity.vo;

import java.time.LocalDateTime;

import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 分类同步数据视图对象
 * 用于 Neo4j 同步接口
 */
@Data
@AllArgsConstructor
@NoArgsConstructor
@Schema(description = "分类同步数据")
@JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)
public class CategorySyncVO {

    @Schema(description = "分类ID")
    private Long id;

    @Schema(description = "分类名称")
    private String name;

    @Schema(description = "更新时间")
    private LocalDateTime updateTime;
}

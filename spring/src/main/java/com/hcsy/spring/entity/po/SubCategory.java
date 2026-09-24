package com.hcsy.spring.entity.po;

import java.time.LocalDateTime;

import org.springframework.data.annotation.Id;
import org.springframework.data.relational.core.mapping.Table;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

@Data
@Table("sub_category")
@Schema(description = "子分类")
public class SubCategory {
    @Schema(description = "子分类ID")
    @Id
    private Long id;

    @Schema(description = "子分类名称")
    private String name;

    @Schema(description = "父分类ID")
    private Long categoryId;

    @Schema(description = "创建时间")
    private LocalDateTime createTime;

    @Schema(description = "更新时间")
    private LocalDateTime updateTime;
}

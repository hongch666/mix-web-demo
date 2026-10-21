package com.hcsy.spring.entity.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 文章收藏数量响应，返回该文章的收藏总数
 */
@Data
@AllArgsConstructor
@NoArgsConstructor
@Schema(description = "收藏数量")
public class CollectCountVO {
    @Schema(description = "收藏数")
    private Long collectCount;
}

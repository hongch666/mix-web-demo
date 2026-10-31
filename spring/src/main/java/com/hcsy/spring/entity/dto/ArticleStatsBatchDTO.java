package com.hcsy.spring.entity.dto;

import java.util.List;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotEmpty;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 批量查询文章与作者统计数据的请求 DTO
 */
@Data
@AllArgsConstructor
@NoArgsConstructor
@Schema(description = "批量文章统计请求")
public class ArticleStatsBatchDTO {
    @Schema(description = "文章ID列表")
    @NotEmpty(message = "文章ID列表不能为空")
    private List<Long> ids;

    @Schema(description = "作者用户ID列表，用于查询粉丝数，可为空")
    private List<Long> authorIds;
}

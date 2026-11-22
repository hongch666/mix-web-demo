package com.hcsy.spring.entity.projection;

import java.time.LocalDateTime;

/**
 * 文章 Excel 导出结果行，由 DatabaseClient 按列直接映射，避免走实体投影导致关联列丢失
 */
public record ArticleExcelRow(
    Long id,
    String title,
    String content,
    Long userId,
    String username,
    String tags,
    Integer status,
    LocalDateTime createAt,
    LocalDateTime updateAt,
    Integer views,
    Integer subCategoryId,
    String subCategoryName,
    Long categoryId,
    String categoryName,
    Long likeCount,
    Long collectCount,
    Long authorFollowCount) {
}

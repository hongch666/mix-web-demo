package com.hcsy.spring.entity.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 文章收藏状态响应，表示当前用户是否已收藏该文章
 */
@Data
@AllArgsConstructor
@NoArgsConstructor
@Schema(description = "收藏状态")
public class CollectCheckVO {
    @Schema(description = "是否已收藏")
    private Boolean collected;
}

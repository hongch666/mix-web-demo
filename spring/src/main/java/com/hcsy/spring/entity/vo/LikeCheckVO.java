package com.hcsy.spring.entity.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 文章点赞状态响应，表示当前用户是否已点赞该文章
 */
@Data
@AllArgsConstructor
@NoArgsConstructor
@Schema(description = "点赞状态")
public class LikeCheckVO {
    @Schema(description = "是否已点赞")
    private Boolean liked;
}

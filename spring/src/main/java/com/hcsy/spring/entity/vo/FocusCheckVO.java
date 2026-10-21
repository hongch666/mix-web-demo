package com.hcsy.spring.entity.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 用户关注状态响应，表示当前用户是否已关注目标用户
 */
@Data
@AllArgsConstructor
@NoArgsConstructor
@Schema(description = "关注状态")
public class FocusCheckVO {
    @Schema(description = "是否已关注")
    private Boolean focused;
}

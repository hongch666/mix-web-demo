package com.hcsy.spring.entity.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotNull;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@AllArgsConstructor
@NoArgsConstructor
@Schema(description = "用户关注请求")
public class FocusDTO {
    @Schema(description = "发起关注的用户ID")
    @NotNull(message = "用户ID不能为空")
    private Long userId;

    @Schema(description = "被关注用户ID")
    @NotNull(message = "关注用户ID不能为空")
    private Long focusId;
}

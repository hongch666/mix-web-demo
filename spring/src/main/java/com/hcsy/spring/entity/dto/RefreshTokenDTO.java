package com.hcsy.spring.entity.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotBlank;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
@Schema(description = "刷新访问令牌请求")
public class RefreshTokenDTO {

    @Schema(description = "刷新令牌")
    @NotBlank(message = "refreshToken 不能为空")
    private String refreshToken;
}

package com.hcsy.spring.entity.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 网关认证通过后返回的身份信息
 */
@Data
@AllArgsConstructor
@NoArgsConstructor
@Schema(description = "网关认证身份")
public class AuthIdentityDTO {
    @Schema(description = "用户ID")
    private Long userId;

    @Schema(description = "用户名")
    private String username;

    @Schema(description = "会话ID")
    private String sessionId;
}

package com.hcsy.spring.entity.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.Pattern;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 管理员重置密码请求，携带可选的指定密码摘要，留空则使用配置中的重置密码
 */
@Data
@AllArgsConstructor
@NoArgsConstructor
@Schema(description = "管理员重置密码请求")
public class AdminResetPasswordDTO {
    @Schema(description = "指定密码的SHA256摘要（64位十六进制），留空则使用配置的重置密码")
    @Pattern(regexp = "^$|^[a-fA-F0-9]{64}$", message = "密码必须为64位SHA256摘要")
    private String password;
}

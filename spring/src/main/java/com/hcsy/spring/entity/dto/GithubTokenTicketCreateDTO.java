package com.hcsy.spring.entity.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 为指定用户创建 GitHub 登录一次性票据的请求，携带用户ID与用户名
 */
@Data
@AllArgsConstructor
@NoArgsConstructor
@Schema(description = "创建 GitHub 登录票据请求")
public class GithubTokenTicketCreateDTO {
    @Schema(description = "用户ID")
    @NotNull(message = "用户ID不能为空")
    private Long userId;

    @Schema(description = "用户名")
    @NotBlank(message = "用户名不能为空")
    private String username;
}

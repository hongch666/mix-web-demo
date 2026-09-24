package com.hcsy.spring.entity.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotBlank;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * GitHub 用户内部创建/更新 DTO（供 NestJS 内部远程调用）
 */
@Data
@AllArgsConstructor
@NoArgsConstructor
@Schema(description = "GitHub 用户内部同步请求")
public class GithubUserInternalDTO {
    @Schema(description = "GitHub 用户ID")
    @NotBlank(message = "GitHub ID不能为空")
    private String githubId;

    @Schema(description = "GitHub 登录名")
    @NotBlank(message = "GitHub 登录名不能为空")
    private String githubLogin;

    @Schema(description = "GitHub 显示名")
    private String githubName;

    @Schema(description = "GitHub 主页地址")
    private String githubUrl;

    @Schema(description = "头像地址")
    private String avatarUrl;

    @Schema(description = "邮箱")
    private String email;
}

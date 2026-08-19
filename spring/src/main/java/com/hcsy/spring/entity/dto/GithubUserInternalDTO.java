package com.hcsy.spring.entity.dto;

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
public class GithubUserInternalDTO {
    @NotBlank(message = "GitHub ID不能为空")
    private String githubId;

    @NotBlank(message = "GitHub 登录名不能为空")
    private String githubLogin;

    private String githubName;
    private String githubUrl;
    private String avatarUrl;
    private String email;
}

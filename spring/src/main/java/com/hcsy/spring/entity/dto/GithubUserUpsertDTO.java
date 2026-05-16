package com.hcsy.spring.entity.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.Data;

@Data
public class GithubUserUpsertDTO {
    @NotBlank(message = "GitHub ID不能为空")
    private String githubId;
    @NotBlank(message = "GitHub 登录名不能为空")
    private String githubLogin;
    private String githubName;
    private String githubUrl;
    private String avatarUrl;
    private String email;
}

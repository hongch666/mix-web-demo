package com.hcsy.spring.entity.vo;

import java.time.LocalDateTime;

import com.fasterxml.jackson.annotation.JsonProperty;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@AllArgsConstructor
@NoArgsConstructor
@Schema(description = "用户视图")
public class UserVO {
    @Schema(description = "用户ID")
    private Long id;

    @Schema(description = "GitHub 用户ID")
    private Long githubId;

    @Schema(description = "GitHub 登录名")
    private String githubLogin;

    @Schema(description = "GitHub 主页地址")
    private String githubUrl;

    @Schema(description = "密码")
    @JsonProperty(access = JsonProperty.Access.WRITE_ONLY)
    private String password;

    @Schema(description = "用户名")
    private String name;

    @Schema(description = "年龄")
    private Integer age;

    @Schema(description = "邮箱")
    private String email;

    @Schema(description = "角色")
    private String role;

    @Schema(description = "头像地址")
    private String img;

    @Schema(description = "个性签名")
    private String signature;

    @Schema(description = "认证来源")
    private String authProvider;

    @Schema(description = "最近登录时间")
    private LocalDateTime lastLoginAt;

    @Schema(description = "登录状态，1在线 0离线")
    private Integer loginStatus;

    @Schema(description = "在线设备数")
    private Long onlineDeviceCount;
}

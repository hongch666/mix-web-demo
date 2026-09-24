package com.hcsy.spring.entity.po;

import java.time.LocalDateTime;

import org.springframework.data.annotation.Id;
import org.springframework.data.annotation.Transient;
import org.springframework.data.relational.core.mapping.Table;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

@Data
@Table("user")
@Schema(description = "用户")
public class User {
    @Schema(description = "用户ID")
    @Id
    private Long id;

    @Schema(description = "GitHub 用户ID")
    private Long githubId;

    @Schema(description = "GitHub 登录名")
    private String githubLogin;

    @Schema(description = "GitHub 主页地址")
    private String githubUrl;

    @Schema(description = "密码")
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

    @Schema(description = "创建时间")
    private LocalDateTime createAt;

    @Schema(description = "更新时间")
    private LocalDateTime updateAt;

    @Schema(description = "登录状态，1在线 0离线")
    @Transient
    private Integer loginStatus;
}

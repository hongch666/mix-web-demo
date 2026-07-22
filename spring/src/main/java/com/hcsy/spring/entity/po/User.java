package com.hcsy.spring.entity.po;

import java.time.LocalDateTime;

import org.springframework.data.annotation.Id;
import org.springframework.data.annotation.Transient;
import org.springframework.data.relational.core.mapping.Table;

import lombok.Data;

@Data
@Table("user")
public class User {
    @Id
    private Long id;
    private Long githubId;
    private String githubLogin;
    private String githubUrl;
    private String password;
    private String name;
    private Integer age;
    private String email;
    private String role;
    private String img;
    private String signature;
    private String authProvider;
    private LocalDateTime lastLoginAt;
    private LocalDateTime createAt;
    private LocalDateTime updateAt;

    // selectUsersWithLoginStatus 动态生成的列，数据库表中不存在
    @Transient
    private Integer loginStatus;
}

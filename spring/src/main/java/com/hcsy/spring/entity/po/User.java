package com.hcsy.spring.entity.po;

import java.time.LocalDateTime;

import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;

import lombok.Data;

@Data
@TableName("user") // 对应数据库中的表名
public class User {
    @TableId
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
    @TableField(exist = false)
    private Integer loginStatus;
}

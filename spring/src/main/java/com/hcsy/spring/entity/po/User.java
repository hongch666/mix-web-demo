package com.hcsy.spring.entity.po;

import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

@Data
@TableName("user") // 对应数据库中的表名
public class User {
    @TableId
    private Long id;
    private String password;
    private String name;
    private Integer age;
    private String email;
    private String role;
    private String img;
    private String signature;
    // 非数据库字段
    private transient Integer loginStatus; // 登录状态，1表示在线，0表示离线
}

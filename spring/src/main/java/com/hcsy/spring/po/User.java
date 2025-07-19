package com.hcsy.spring.po;

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
}

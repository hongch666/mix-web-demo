package com.hcsy.spring.po;

import java.time.LocalDateTime;

import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;

import lombok.Data;

@Data
@TableName("sub_category") // 对应数据库中的表名
public class SubCategory {
    @TableId
    private Long id;
    private String name;
    private Long categoryId; // 关联的主分类ID
    private LocalDateTime createTime;
    private LocalDateTime updateTime;
}

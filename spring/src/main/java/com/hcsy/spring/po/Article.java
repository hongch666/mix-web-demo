package com.hcsy.spring.po;

import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@TableName("articles") // 对应数据库中的表名
public class Article {
    @TableId
    private Long id;
    private String title;
    private String content;
    private Long userId;
    private String tags; // 标签用逗号分隔
    private Integer status; // 0=草稿，1=已发布
    private Integer views; // 浏览量
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}

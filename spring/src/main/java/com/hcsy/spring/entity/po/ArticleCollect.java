package com.hcsy.spring.entity.po;

import java.time.LocalDateTime;

import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;

import lombok.Data;

@Data
@TableName("collects")
public class ArticleCollect {
    @TableId
    private Long id;
    private Long articleId;
    private Long userId;
    private LocalDateTime createdTime;
}

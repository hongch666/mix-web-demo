package com.hcsy.spring.entity.po;

import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@TableName("collects")
public class ArticleCollect {
    @TableId
    private Long id;
    private Long articleId;
    private Long userId;
    private LocalDateTime createdTime;
}

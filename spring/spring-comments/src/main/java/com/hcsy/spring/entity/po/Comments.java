package com.hcsy.spring.entity.po;

import java.time.LocalDateTime;

import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;

import lombok.Data;

@Data
@TableName("comments") // 对应数据库中的表名
public class Comments {
    @TableId
    private Long id;
    private String content;
    private Double star; // 星级评分，1~10
    private Long articleId;
    private Long userId;
    private LocalDateTime createTime;
    private LocalDateTime updateTime;
}

package com.hcsy.spring.entity.vo;

import lombok.Data;

@Data
public class CommentsVO {
    private Long id;
    private String content;
    private Double star;
    private String username;
    private String articleTitle;
    private String createTime;
    private String updateTime;
}

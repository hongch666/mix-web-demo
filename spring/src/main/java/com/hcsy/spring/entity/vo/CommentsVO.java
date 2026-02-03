package com.hcsy.spring.entity.vo;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@AllArgsConstructor
@NoArgsConstructor
public class CommentsVO {
    private Long id;
    private String content;
    private Double star;
    private String username;
    private String pic;
    private String articleTitle;
    private String createTime;
    private String updateTime;
}

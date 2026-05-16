package com.hcsy.spring.entity.vo;

import lombok.Data;

@Data
public class ArticleStatisticVO {
    private Long articleId;
    private Integer views;
    private Integer likeCount;
    private Integer collectCount;
    private Integer authorFollowCount;
}

package com.hcsy.spring.entity.vo;

import lombok.Data;

@Data
public class ArticleStatisticsAnalyzeVO {
    private Long totalViews;
    private Long totalArticles;
    private Long activeAuthors;
    private Double averageViews;
    private Long totalLikes;
    private Double averageLikes;
    private Long totalCollects;
    private Double averageCollects;
}

package com.hcsy.spring.entity.vo;

import java.time.LocalDateTime;

import com.fasterxml.jackson.annotation.JsonProperty;

import lombok.Data;

@Data
public class ArticleSearchDocVO {
    private Long id;
    private String title;
    private String content;
    private Long userId;
    private String username;
    private String tags;
    private Integer status;
    private Integer views;
    private Integer likeCount;
    private Integer collectCount;
    private Integer authorFollowCount;
    @JsonProperty("category_name")
    private String categoryName;
    @JsonProperty("sub_category_name")
    private String subCategoryName;
    @JsonProperty("create_at")
    private LocalDateTime createAt;
    @JsonProperty("update_at")
    private LocalDateTime updateAt;
    @JsonProperty("ai_score")
    private Double aiScore;
    @JsonProperty("user_score")
    private Double userScore;
    @JsonProperty("ai_comment_count")
    private Integer aiCommentCount;
    @JsonProperty("user_comment_count")
    private Integer userCommentCount;
}

package com.hcsy.spring.entity.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.Data;

@Data
public class AiCommentItemDTO {
    @NotNull(message = "用户ID不能为空")
    private Long userId;
    @NotBlank(message = "评论内容不能为空")
    private String content;
    @NotNull(message = "评分不能为空")
    private Double star;
}

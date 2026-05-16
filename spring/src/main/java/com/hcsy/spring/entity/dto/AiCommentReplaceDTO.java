package com.hcsy.spring.entity.dto;

import java.util.List;

import jakarta.validation.Valid;
import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.NotNull;
import lombok.Data;

@Data
public class AiCommentReplaceDTO {
    @NotNull(message = "文章ID不能为空")
    private Long articleId;
    @Valid
    @NotEmpty(message = "AI评论不能为空")
    private List<AiCommentItemDTO> comments;
}

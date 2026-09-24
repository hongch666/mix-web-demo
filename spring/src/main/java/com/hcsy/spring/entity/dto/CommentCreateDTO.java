package com.hcsy.spring.entity.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.DecimalMax;
import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@AllArgsConstructor
@NoArgsConstructor
@Schema(description = "创建评论请求")
public class CommentCreateDTO {
    @Schema(description = "评论内容")
    @NotBlank(message = "评论内容不能为空")
    @Size(min = 1, max = 200, message = "评论内容长度应在1~200之间")
    private String content;

    @Schema(description = "星级评分，1到10")
    @NotNull(message = "星级评分不能为空")
    @DecimalMin(value = "1", message = "星级评分应在1~10之间")
    @DecimalMax(value = "10", message = "星级评分应在1~10之间")
    private Double star; // 星级评分，1~10

    @Schema(description = "文章标题")
    @NotNull(message = "文章标题不能为空")
    @Size(min = 1, message = "文章标题不能为空")
    private String articleTitle;

    @Schema(description = "评论用户名")
    @NotNull(message = "用户名不能为空")
    @Size(min = 1, message = "用户名不能为空")
    private String username;
}

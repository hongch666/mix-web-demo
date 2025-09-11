package com.hcsy.spring.entity.dto;

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
public class CommentCreateDTO {
    @NotBlank(message = "评论内容不能为空")
    @Size(min = 1, max = 200, message = "评论内容长度应在1~200之间")
    private String content;

    @NotNull(message = "星级评分不能为空")
    @DecimalMin(value = "1", message = "星级评分应在1~10之间")
    @DecimalMax(value = "10", message = "星级评分应在1~10之间")
    private Double star; // 星级评分，1~10

    @NotNull(message = "文章标题不能为空")
    @Size(min = 1, message = "文章标题不能为空")
    private String articleTitle;

    @NotNull(message = "用户名不能为空")
    @Size(min = 1, message = "用户名不能为空")
    private String username;

}

package com.hcsy.spring.entity.dto;

import jakarta.validation.constraints.*;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@AllArgsConstructor
@NoArgsConstructor
public class ArticleCreateDTO {

    @NotBlank(message = "文章标题不能为空")
    @Size(min = 1, max = 200, message = "文章标题长度应在1~200之间")
    private String title;

    @NotBlank(message = "文章内容不能为空")
    private String content;

    // @NotNull(message = "用户ID不能为空")
    // private Long userId;

    @NotBlank(message = "用户名不能为空")
    @Size(min = 1, max = 50, message = "用户名长度应在1~50之间")
    private String username;

    @Size(max = 200, message = "标签字符串长度不能超过200个字符")
    private String tags; // 多个标签用英文逗号分隔

    @NotNull(message = "状态不能为空")
    @Min(value = 0, message = "状态值无效")
    @Max(value = 1, message = "状态值无效")
    private Integer status;

    @NotNull(message = "子分类ID不能为空")
    @Min(value = 1, message = "子分类ID必须大于0")
    private Integer subCategoryId;
}

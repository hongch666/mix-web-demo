package com.hcsy.spring.dto;

import jakarta.validation.constraints.*;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.EqualsAndHashCode;
import lombok.NoArgsConstructor;

@Data
@EqualsAndHashCode(callSuper = false)
@AllArgsConstructor
@NoArgsConstructor
public class ArticleUpdateDTO extends ArticleCreateDTO {

    @NotNull(message = "文章ID不能为空")
    @Min(value = 1, message = "文章ID必须大于0")
    private Long id;
}

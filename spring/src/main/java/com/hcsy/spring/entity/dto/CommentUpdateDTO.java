package com.hcsy.spring.entity.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.EqualsAndHashCode;
import lombok.NoArgsConstructor;

@Data
@EqualsAndHashCode(callSuper = false)
@AllArgsConstructor
@NoArgsConstructor
@Schema(description = "更新评论请求")
public class CommentUpdateDTO extends CommentCreateDTO {
    @Schema(description = "评论ID")
    @NotNull(message = "id不能为空")
    @Min(value = 0, message = "id不能小于0")
    private Integer id;
}

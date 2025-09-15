package com.hcsy.spring.entity.dto;

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
public class CommentUpdateDTO extends CommentCreateDTO {
    @NotNull(message = "id不能为空")
    @Min(value = 0, message = "id不能小于0")
    private Integer id;

}

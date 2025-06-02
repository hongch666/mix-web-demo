package com.hcsy.spring.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.EqualsAndHashCode;
import lombok.NoArgsConstructor;
import jakarta.validation.constraints.*;

@Data
@EqualsAndHashCode(callSuper = false)
@AllArgsConstructor
@NoArgsConstructor
public class UserUpdateDTO extends UserCreateDTO {

    @NotNull(message = "id不能为空")
    @Min(value = 0, message = "id不能小于0")
    private Integer id;
}

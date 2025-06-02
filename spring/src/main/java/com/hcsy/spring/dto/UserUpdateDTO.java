package com.hcsy.spring.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import jakarta.validation.constraints.*;

@Data
@AllArgsConstructor
@NoArgsConstructor
public class UserUpdateDTO extends UserCreateDTO {

    @NotNull(message = "id不能为空")
    @Min(value = 0, message = "id不能小于0")
    private Integer id;
}

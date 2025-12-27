package com.hcsy.spring.entity.dto;

import jakarta.validation.constraints.NotNull;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@AllArgsConstructor
@NoArgsConstructor
public class FocusDTO {

    @NotNull(message = "用户ID不能为空")
    private Long userId;

    @NotNull(message = "关注用户ID不能为空")
    private Long focusId;
}

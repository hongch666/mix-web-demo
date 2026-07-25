package com.hcsy.spring.entity.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@AllArgsConstructor
@NoArgsConstructor
public class GithubTokenTicketCreateDTO {
    @NotNull(message = "用户ID不能为空")
    private Long userId;

    @NotBlank(message = "用户名不能为空")
    private String username;
}

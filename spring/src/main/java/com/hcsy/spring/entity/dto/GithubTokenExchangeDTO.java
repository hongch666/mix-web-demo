package com.hcsy.spring.entity.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@AllArgsConstructor
@NoArgsConstructor
public class GithubTokenExchangeDTO {
    @NotBlank(message = "票据不能为空")
    private String ticket;
}

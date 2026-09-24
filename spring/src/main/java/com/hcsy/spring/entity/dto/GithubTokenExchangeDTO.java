package com.hcsy.spring.entity.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotBlank;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@AllArgsConstructor
@NoArgsConstructor
@Schema(description = "GitHub 登录票据换取令牌请求")
public class GithubTokenExchangeDTO {
    @Schema(description = "一次性登录票据")
    @NotBlank(message = "票据不能为空")
    private String ticket;
}

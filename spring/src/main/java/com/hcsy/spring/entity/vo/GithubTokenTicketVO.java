package com.hcsy.spring.entity.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@Schema(description = "GitHub 登录票据")
public class GithubTokenTicketVO {
    @Schema(description = "一次性登录票据")
    private String ticket;

    @Schema(description = "有效期，单位秒")
    private Long expiresIn;
}

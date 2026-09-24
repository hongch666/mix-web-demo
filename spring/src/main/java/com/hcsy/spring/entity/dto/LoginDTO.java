package com.hcsy.spring.entity.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@AllArgsConstructor
@NoArgsConstructor
@Schema(description = "用户名密码登录请求")
public class LoginDTO {
    @Schema(description = "登录密码")
    @NotBlank(message = "密码不能为空")
    @Size(min = 3, max = 20, message = "密码长度必须在3到20个字符之间")
    private String password;

    @Schema(description = "用户名")
    @NotBlank(message = "用户名不能为空")
    @Size(min = 3, max = 20, message = "用户名长度必须在3到20个字符之间")
    private String name;

    @Schema(description = "图形验证码ID")
    @NotBlank(message = "图形验证码ID不能为空")
    private String captchaId;

    @Schema(description = "图形验证码文本")
    @NotBlank(message = "图形验证码不能为空")
    @Size(min = 4, max = 4, message = "图形验证码为4位")
    private String captchaText;
}

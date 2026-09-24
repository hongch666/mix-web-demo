package com.hcsy.spring.entity.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@AllArgsConstructor
@NoArgsConstructor
@Schema(description = "创建用户请求")
public class UserCreateDTO {
    @Schema(description = "登录密码，留空表示不修改")
    @Pattern(regexp = "^$|^(?=.*[A-Za-z])(?=.*\\d).{8,20}$", message = "密码必须为8到20位且包含字母和数字")
    private String password;

    @Schema(description = "用户名")
    @NotBlank(message = "用户名不能为空")
    private String name;

    @Schema(description = "年龄")
    @NotNull(message = "年龄不能为空")
    @Min(value = 0, message = "年龄不能小于0岁")
    @Max(value = 150, message = "年龄不能大于150岁")
    private Integer age;

    @Schema(description = "邮箱")
    @NotBlank(message = "邮箱不能为空")
    @Email(message = "邮箱格式不正确")
    private String email;

    @Schema(description = "头像地址")
    @Size(max = 255, message = "头像链接长度不能超过255个字符")
    private String img;

    @Schema(description = "个性签名")
    @Size(max = 255, message = "个性签名长度不能超过255个字符")
    private String signature;
}

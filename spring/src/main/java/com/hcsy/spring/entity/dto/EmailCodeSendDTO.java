package com.hcsy.spring.entity.dto;

import jakarta.validation.constraints.Email;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@AllArgsConstructor
@NoArgsConstructor
public class EmailCodeSendDTO {
    @Email(message = "邮箱格式不正确")
    private String email;

    private String type;
}

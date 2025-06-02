package com.hcsy.spring.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@AllArgsConstructor
@NoArgsConstructor
public class UserCreateDTO {

    private String password;

    private String name;

    private Integer age;

    private String email;
}

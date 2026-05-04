package com.hcsy.spring.entity.dto;

import com.hcsy.spring.common.utils.Constants;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@AllArgsConstructor
@NoArgsConstructor
public class GithubTokenTicketCreateDTO {
    @NotNull(message = Constants.GITHUB_TOKEN_TICKET_USER_ID_REQUIRED)
    private Long userId;

    @NotBlank(message = Constants.GITHUB_TOKEN_TICKET_USERNAME_REQUIRED)
    private String username;
}

package com.hcsy.spring.entity.dto;

import com.hcsy.spring.common.constants.Messages;

import jakarta.validation.constraints.NotBlank;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@AllArgsConstructor
@NoArgsConstructor
public class GithubTokenExchangeDTO {
    @NotBlank(message = Messages.GITHUB_TOKEN_EXCHANGE_TICKET_REQUIRED)
    private String ticket;
}

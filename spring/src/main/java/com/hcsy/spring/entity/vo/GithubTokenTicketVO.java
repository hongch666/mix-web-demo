package com.hcsy.spring.entity.vo;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class GithubTokenTicketVO {
    private String ticket;
    private Long expiresIn;
}

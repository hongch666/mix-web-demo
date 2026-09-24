package com.hcsy.spring.entity.vo;

import java.util.List;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@Schema(description = "用户分页结果")
public class UserListVO {
    @Schema(description = "总记录数")
    private Long total;

    @Schema(description = "用户列表")
    private List<UserVO> list;
}

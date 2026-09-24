package com.hcsy.spring.entity.vo;

import java.time.LocalDateTime;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@AllArgsConstructor
@NoArgsConstructor
@Schema(description = "关注用户")
public class FocusUserVO {
    @Schema(description = "用户ID")
    private Long id;

    @Schema(description = "用户名")
    private String name;

    @Schema(description = "年龄")
    private Integer age;

    @Schema(description = "邮箱")
    private String email;

    @Schema(description = "头像地址")
    private String img;

    @Schema(description = "个性签名")
    private String signature;

    @Schema(description = "角色")
    private String role;

    @Schema(description = "关注时间")
    private LocalDateTime focusedTime;
}

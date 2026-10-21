package com.hcsy.spring.entity.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 图形验证码响应，包含验证码ID与 Base64 编码的验证码图片
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@Schema(description = "图形验证码")
public class ImageCaptchaVO {
    @Schema(description = "图形验证码ID")
    private String captchaId;

    @Schema(description = "图形验证码 Base64")
    private String imageBase64;
}

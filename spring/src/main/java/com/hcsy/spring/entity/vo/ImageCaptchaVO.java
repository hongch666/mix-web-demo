package com.hcsy.spring.entity.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

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

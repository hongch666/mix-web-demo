package com.hcsy.spring.api.service.impl;

import java.awt.Color;
import java.awt.Font;
import java.awt.Graphics2D;
import java.awt.RenderingHints;
import java.awt.image.BufferedImage;
import java.io.ByteArrayOutputStream;
import java.security.SecureRandom;
import java.util.Base64;
import java.util.UUID;

import javax.imageio.ImageIO;

import org.springframework.stereotype.Service;

import com.hcsy.spring.api.service.ImageCaptchaService;
import com.hcsy.spring.common.utils.Constants;
import com.hcsy.spring.common.utils.RedisUtil;
import com.hcsy.spring.common.utils.SimpleLogger;
import com.hcsy.spring.entity.vo.ImageCaptchaVO;

import lombok.RequiredArgsConstructor;

/**
 * 图形验证码服务实现
 */
@Service
@RequiredArgsConstructor
public class ImageCaptchaServiceImpl implements ImageCaptchaService {
    private static final String CAPTCHA_PREFIX = "image:captcha:";
    private static final long CAPTCHA_EXPIRY = 5 * 60;
    private static final int CAPTCHA_WIDTH = 130;
    private static final int CAPTCHA_HEIGHT = 40;
    private static final int CAPTCHA_LENGTH = 4;
    private static final char[] CAPTCHA_CHARS = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789".toCharArray();

    private final RedisUtil redisUtil;
    private final SimpleLogger logger;
    private final SecureRandom secureRandom = new SecureRandom();

    @Override
    public ImageCaptchaVO createCaptcha() {
        String captchaId = UUID.randomUUID().toString().replace("-", "");
        String captchaText = generateCaptchaText();
        String key = buildCaptchaKey(captchaId);

        redisUtil.set(key, captchaText, CAPTCHA_EXPIRY);
        logger.info(Constants.IMAGE_CAPTCHA_SAVE + captchaId);

        return ImageCaptchaVO.builder()
                .captchaId(captchaId)
                .imageBase64(generateCaptchaBase64(captchaText))
                .build();
    }

    @Override
    public boolean verifyCaptcha(String captchaId, String captchaText) {
        String storedCaptcha = redisUtil.get(buildCaptchaKey(captchaId));
        if (storedCaptcha == null || captchaText == null) {
            logger.info(Constants.IMAGE_CAPTCHA_EXPIRED + captchaId);
            return false;
        }

        boolean matched = storedCaptcha.equalsIgnoreCase(captchaText.trim());
        if (!matched) {
            logger.info(Constants.IMAGE_CAPTCHA_VERIFY_FAIL + captchaId);
            return false;
        }

        logger.info(Constants.IMAGE_CAPTCHA_VERIFY_SUCCESS + captchaId);
        return true;
    }

    @Override
    public void deleteCaptcha(String captchaId) {
        redisUtil.delete(buildCaptchaKey(captchaId));
        logger.info(Constants.IMAGE_CAPTCHA_DELETE + captchaId);
    }

    private String buildCaptchaKey(String captchaId) {
        return CAPTCHA_PREFIX + captchaId;
    }

    private String generateCaptchaText() {
        StringBuilder builder = new StringBuilder(CAPTCHA_LENGTH);
        for (int i = 0; i < CAPTCHA_LENGTH; i++) {
            builder.append(CAPTCHA_CHARS[secureRandom.nextInt(CAPTCHA_CHARS.length)]);
        }
        return builder.toString();
    }

    private String generateCaptchaBase64(String captchaText) {
        BufferedImage image = new BufferedImage(CAPTCHA_WIDTH, CAPTCHA_HEIGHT, BufferedImage.TYPE_INT_RGB);
        Graphics2D graphics = image.createGraphics();
        try {
            graphics.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
            graphics.setColor(new Color(245, 247, 250));
            graphics.fillRect(0, 0, CAPTCHA_WIDTH, CAPTCHA_HEIGHT);

            drawNoise(graphics);
            drawCaptchaText(graphics, captchaText);

            ByteArrayOutputStream outputStream = new ByteArrayOutputStream();
            ImageIO.write(image, "png", outputStream);
            return "data:image/png;base64," + Base64.getEncoder().encodeToString(outputStream.toByteArray());
        } catch (Exception e) {
            throw new IllegalStateException(Constants.IMAGE_CAPTCHA_GENERATE_FAIL, e);
        } finally {
            graphics.dispose();
        }
    }

    private void drawNoise(Graphics2D graphics) {
        for (int i = 0; i < 12; i++) {
            graphics.setColor(randomColor(160, 220));
            int x1 = secureRandom.nextInt(CAPTCHA_WIDTH);
            int y1 = secureRandom.nextInt(CAPTCHA_HEIGHT);
            int x2 = secureRandom.nextInt(CAPTCHA_WIDTH);
            int y2 = secureRandom.nextInt(CAPTCHA_HEIGHT);
            graphics.drawLine(x1, y1, x2, y2);
        }

        for (int i = 0; i < 80; i++) {
            graphics.setColor(randomColor(180, 255));
            int x = secureRandom.nextInt(CAPTCHA_WIDTH);
            int y = secureRandom.nextInt(CAPTCHA_HEIGHT);
            graphics.drawRect(x, y, 1, 1);
        }
    }

    private void drawCaptchaText(Graphics2D graphics, String captchaText) {
        graphics.setFont(new Font("Arial", Font.BOLD, 28));
        for (int i = 0; i < captchaText.length(); i++) {
            graphics.setColor(randomColor(20, 120));
            int x = 18 + i * 24;
            int y = 28 + secureRandom.nextInt(6);
            graphics.drawString(String.valueOf(captchaText.charAt(i)), x, y);
        }
    }

    private Color randomColor(int min, int max) {
        int realMin = Math.max(0, min);
        int realMax = Math.min(255, max);
        int bound = realMax - realMin + 1;
        int red = realMin + secureRandom.nextInt(bound);
        int green = realMin + secureRandom.nextInt(bound);
        int blue = realMin + secureRandom.nextInt(bound);
        return new Color(red, green, blue);
    }
}

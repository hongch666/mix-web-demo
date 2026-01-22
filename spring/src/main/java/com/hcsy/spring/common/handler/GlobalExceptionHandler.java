package com.hcsy.spring.common.handler;

import com.hcsy.spring.common.exceptions.BusinessException;
import com.hcsy.spring.common.utils.Result;
import com.hcsy.spring.common.utils.SimpleLogger;

import lombok.RequiredArgsConstructor;

import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

@RestControllerAdvice
@RequiredArgsConstructor
public class GlobalExceptionHandler {
    private final SimpleLogger logger;

    /**
     * 处理业务异常
     */
    @ExceptionHandler(BusinessException.class)
    public Result handleBusinessException(BusinessException ex) {
        logger.error("捕获到业务异常: " + ex.getMessage(), ex);
        return Result.error(ex.getErrorMessage());
    }

    /**
     * 处理其他异常
     */
    @ExceptionHandler(Exception.class)
    public Result handleException(Exception ex) {
        logger.error("捕获到系统异常: " + ex.getMessage(), ex);
        return Result.error("Spring服务器错误");
    }
}
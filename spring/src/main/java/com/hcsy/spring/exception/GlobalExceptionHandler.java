package com.hcsy.spring.exception;

import com.hcsy.spring.po.Result;

import lombok.extern.slf4j.Slf4j;

import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

@RestControllerAdvice
@Slf4j
public class GlobalExceptionHandler {
    @ExceptionHandler(Exception.class)
    public Result ex(Exception ex) {
        log.error("捕获到异常: " + ex.getMessage());
        return Result.error(ex.getMessage());
    }
}

package com.hcsy.gateway.common;

public class BusinessException extends RuntimeException {
    private final int statusCode;
    private final String error;

    public BusinessException(String message, int statusCode, String error) {
        super(message);
        this.statusCode = statusCode;
        this.error = error;
    }

    public BusinessException(String message) {
        this(message, HttpCode.INTERNAL_SERVER_ERROR, "GATEWAY_SERVER_ERROR");
    }

    public BusinessException(String message, int statusCode) {
        this(message, statusCode, "GATEWAY_SERVER_ERROR");
    }

    public int getStatusCode() {
        return statusCode;
    }

    public String getError() {
        return error;
    }

    public static BusinessException unauthorized(String message, String error) {
        return new BusinessException(message, HttpCode.UNAUTHORIZED, error);
    }

    public static BusinessException forbidden(String message, String error) {
        return new BusinessException(message, HttpCode.FORBIDDEN, error);
    }

    public static BusinessException tooManyRequests(String message, String error) {
        return new BusinessException(message, HttpCode.TOO_MANY_REQUESTS, error);
    }

    public static BusinessException internalServerError(String message, String error) {
        return new BusinessException(message, HttpCode.INTERNAL_SERVER_ERROR, error);
    }

    public static BusinessException badGateway(String message, String error) {
        return new BusinessException(message, HttpCode.BAD_GATEWAY, error);
    }

    public static BusinessException serviceUnavailable(String message, String error) {
        return new BusinessException(message, HttpCode.SERVICE_UNAVAILABLE, error);
    }

    public static BusinessException gatewayTimeout(String message, String error) {
        return new BusinessException(message, HttpCode.GATEWAY_TIMEOUT, error);
    }
}

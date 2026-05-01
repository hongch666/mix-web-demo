package com.hcsy.spring.common.exceptions;

/**
 * 业务异常类，用于普通的业务错误抛出异常
 */
public class BusinessException extends RuntimeException {
    private int httpStatus;
    private String errorCode;
    private String errorMessage;

    public BusinessException(String errorMessage) {
        super(errorMessage);
        this.httpStatus = 500;
        this.errorMessage = errorMessage;
    }

    public BusinessException(int httpStatus, String errorMessage) {
        super(errorMessage);
        this.httpStatus = httpStatus;
        this.errorMessage = errorMessage;
    }

    public BusinessException(String errorCode, String errorMessage) {
        super(errorMessage);
        this.httpStatus = 500;
        this.errorCode = errorCode;
        this.errorMessage = errorMessage;
    }

    public BusinessException(int httpStatus, String errorCode, String errorMessage) {
        super(errorMessage);
        this.httpStatus = httpStatus;
        this.errorCode = errorCode;
        this.errorMessage = errorMessage;
    }

    public BusinessException(String errorMessage, Throwable cause) {
        super(errorMessage, cause);
        this.httpStatus = 500;
        this.errorMessage = errorMessage;
    }

    public BusinessException(int httpStatus, String errorMessage, Throwable cause) {
        super(errorMessage, cause);
        this.httpStatus = httpStatus;
        this.errorMessage = errorMessage;
    }

    public BusinessException(String errorCode, String errorMessage, Throwable cause) {
        super(errorMessage, cause);
        this.httpStatus = 500;
        this.errorCode = errorCode;
        this.errorMessage = errorMessage;
    }

    public BusinessException(int httpStatus, String errorCode, String errorMessage, Throwable cause) {
        super(errorMessage, cause);
        this.httpStatus = httpStatus;
        this.errorCode = errorCode;
        this.errorMessage = errorMessage;
    }

    public int getHttpStatus() {
        return httpStatus;
    }

    public String getErrorCode() {
        return errorCode;
    }

    public String getErrorMessage() {
        return errorMessage != null ? errorMessage : getMessage();
    }
}

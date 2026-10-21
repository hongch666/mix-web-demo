package com.hcsy.spring.common.exceptions;

import com.hcsy.spring.common.constants.HttpCode;

/**
 * 业务异常类，用于普通的业务错误抛出异常
 * 支持直接构造和 Builder 模式两种创建方式
 */
public class BusinessException extends RuntimeException {
    private int httpStatus;
    private String errorCode;
    private String errorMessage;

    /**
     * 以错误信息构造业务异常，HTTP 状态默认为 500
     */
    public BusinessException(String errorMessage) {
        super(errorMessage);
        this.httpStatus = HttpCode.INTERNAL_SERVER_ERROR;
        this.errorMessage = errorMessage;
    }

    /**
     * 以 HTTP 状态码与错误信息构造业务异常
     */
    public BusinessException(int httpStatus, String errorMessage) {
        super(errorMessage);
        this.httpStatus = httpStatus;
        this.errorMessage = errorMessage;
    }

    /**
     * 以错误码与错误信息构造业务异常，HTTP 状态默认为 500
     */
    public BusinessException(String errorCode, String errorMessage) {
        super(errorMessage);
        this.httpStatus = HttpCode.INTERNAL_SERVER_ERROR;
        this.errorCode = errorCode;
        this.errorMessage = errorMessage;
    }

    /**
     * 以 HTTP 状态码、错误码与错误信息构造业务异常
     */
    public BusinessException(int httpStatus, String errorCode, String errorMessage) {
        super(errorMessage);
        this.httpStatus = httpStatus;
        this.errorCode = errorCode;
        this.errorMessage = errorMessage;
    }

    /**
     * 以错误信息与底层原因构造业务异常，HTTP 状态默认为 500
     */
    public BusinessException(String errorMessage, Throwable cause) {
        super(errorMessage, cause);
        this.httpStatus = HttpCode.INTERNAL_SERVER_ERROR;
        this.errorMessage = errorMessage;
    }

    /**
     * 以 HTTP 状态码、错误信息与底层原因构造业务异常
     */
    public BusinessException(int httpStatus, String errorMessage, Throwable cause) {
        super(errorMessage, cause);
        this.httpStatus = httpStatus;
        this.errorMessage = errorMessage;
    }

    /**
     * 以错误码、错误信息与底层原因构造业务异常，HTTP 状态默认为 500
     */
    public BusinessException(String errorCode, String errorMessage, Throwable cause) {
        super(errorMessage, cause);
        this.httpStatus = HttpCode.INTERNAL_SERVER_ERROR;
        this.errorCode = errorCode;
        this.errorMessage = errorMessage;
    }

    /**
     * 以 HTTP 状态码、错误码、错误信息与底层原因构造业务异常
     */
    public BusinessException(int httpStatus, String errorCode, String errorMessage, Throwable cause) {
        super(errorMessage, cause);
        this.httpStatus = httpStatus;
        this.errorCode = errorCode;
        this.errorMessage = errorMessage;
    }

    /**
     * 创建 Builder 实例
     */
    public static Builder builder() {
        return new Builder();
    }

    /**
     * Builder 模式，用于灵活构建 BusinessException
     */
    public static class Builder {
        private int httpStatus = HttpCode.INTERNAL_SERVER_ERROR;
        private String errorCode;
        private String errorMessage;
        private Throwable cause;

        public Builder httpStatus(int httpStatus) {
            this.httpStatus = httpStatus;
            return this;
        }

        public Builder errorCode(String errorCode) {
            this.errorCode = errorCode;
            return this;
        }

        public Builder errorMessage(String errorMessage) {
            this.errorMessage = errorMessage;
            return this;
        }

        public Builder cause(Throwable cause) {
            this.cause = cause;
            return this;
        }

        public BusinessException build() {
            if (cause != null) {
                if (errorCode != null) {
                    return new BusinessException(httpStatus, errorCode, errorMessage, cause);
                }
                return new BusinessException(httpStatus, errorMessage, cause);
            }
            if (errorCode != null) {
                return new BusinessException(httpStatus, errorCode, errorMessage);
            }
            return new BusinessException(httpStatus, errorMessage);
        }
    }

    /**
     * 返回异常对应的 HTTP 状态码
     */
    public int getHttpStatus() {
        return httpStatus;
    }

    /**
     * 返回业务错误码
     */
    public String getErrorCode() {
        return errorCode;
    }

    /**
     * 返回错误信息，为空时回退到异常消息
     */
    public String getErrorMessage() {
        return errorMessage != null ? errorMessage : getMessage();
    }
}

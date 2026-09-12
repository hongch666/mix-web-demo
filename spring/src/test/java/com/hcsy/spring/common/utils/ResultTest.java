package com.hcsy.spring.common.utils;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNull;

import org.junit.jupiter.api.Test;

import com.hcsy.spring.common.constants.HttpCode;

class ResultTest {
    @Test
    void successFactoriesPopulateExpectedFields() {
        Result<Void> empty = Result.success();
        assertEquals(HttpCode.OK, empty.getCode());
        assertEquals("success", empty.getMsg());
        assertNull(empty.getData());

        Result<String> value = Result.success("payload");
        assertEquals(HttpCode.OK, value.getCode());
        assertEquals("payload", value.getData());
    }

    @Test
    void errorFactoriesKeepMessageAndClearData() {
        Result<Void> generic = Result.error("failed");
        assertEquals(HttpCode.INTERNAL_SERVER_ERROR, generic.getCode());
        assertEquals("failed", generic.getMsg());
        assertNull(generic.getData());

        Result<Void> custom = Result.error(418, "teapot");
        assertEquals(418, custom.getCode());
        assertEquals("teapot", custom.getMsg());
        assertNull(custom.getData());
    }
}

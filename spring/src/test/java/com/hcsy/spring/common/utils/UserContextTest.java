package com.hcsy.spring.common.utils;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNull;

import reactor.util.context.Context;

class UserContextTest {
    @Test
    void writeAndReadContextValues() {
        Context context = UserContext.writeContext(Context.empty(), 42L, "alice", "session-1", "token-1",
            "internal-1");

        assertEquals(42L, UserContext.getUserId(context));
        assertEquals("alice", UserContext.getUsername(context));
        assertEquals("session-1", UserContext.getSessionId(context));
        assertEquals("token-1", UserContext.getToken(context));
        assertEquals("internal-1", UserContext.getInternalToken(context));
    }

    @Test
    void nullValuesDoNotOverwriteExistingValues() {
        Context original = UserContext.writeContext(Context.empty(), 7L, "bob", "s", "t", "it");
        Context updated = UserContext.writeContext(original, null, null, null, null, null);

        assertEquals(7L, UserContext.getUserId(updated));
        assertEquals("bob", UserContext.getUsername(updated));
    }

    @Test
    void missingValuesReturnNull() {
        Context empty = Context.empty();
        assertNull(UserContext.getUserId(empty));
        assertNull(UserContext.getUsername(empty));
        assertNull(UserContext.getSessionId(empty));
        assertNull(UserContext.getToken(empty));
        assertNull(UserContext.getInternalToken(empty));
    }
}

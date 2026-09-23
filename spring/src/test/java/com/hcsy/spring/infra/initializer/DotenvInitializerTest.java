package com.hcsy.spring.infra.initializer;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Map;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.springframework.test.util.ReflectionTestUtils;

import static org.junit.jupiter.api.Assertions.assertEquals;

class DotenvInitializerTest {

    @Test
    @DisplayName("应该解析.env文件并去除注释与引号")
    void shouldParseEnvFile(@TempDir Path tempDir) throws Exception {
        Path envFile = tempDir.resolve(".env");
        Files.writeString(envFile, String.join("\n",
            "# 这是注释行",
            "",
            "DB_HOST=127.0.0.1",
            "DB_NAME=\"demo\"",
            "DB_PASSWORD='secret=value'",
            "  DB_USER = root  "));

        Map<String, String> envMap = ReflectionTestUtils.invokeMethod(
            DotenvInitializer.class, "parseEnvFile", envFile.toFile());

        assertEquals(4, envMap.size());
        assertEquals("127.0.0.1", envMap.get("DB_HOST"));
        assertEquals("demo", envMap.get("DB_NAME"));
        assertEquals("secret=value", envMap.get("DB_PASSWORD"));
        assertEquals("root", envMap.get("DB_USER"));
    }
}

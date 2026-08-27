package com.hcsy.spring.infra.initializer;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.util.HashMap;
import java.util.Map;

import com.hcsy.spring.common.constants.Messages;

import lombok.extern.slf4j.Slf4j;

/**
 * .env文件加载器，用于在应用启动前加载环境变量
 */
@Slf4j
public class DotenvInitializer {

    private static final String DOT_ENV_FILE = ".env";

    /**
     * .env 文件候选路径：依次尝试当前目录、spring 子目录、上级目录，
     * 兼容从项目根目录、spring 目录或 IDE 默认工作目录启动的情况
     */
    private static final String[] CANDIDATE_PATHS = {
        DOT_ENV_FILE,
        "spring/" + DOT_ENV_FILE,
        "../" + DOT_ENV_FILE,
    };

    /**
     * 加载.env文件中的环境变量到系统属性
     */
    public static void loadEnv() {
        try {
            // 按候选路径顺序查找.env文件
            File envFile = findEnvFile();

            if (envFile == null) {
                log.info(Messages.DOTENV_FILE_NOT_EXIST);
                return;
            }

            // 解析.env文件
            Map<String, String> envMap = parseEnvFile(envFile);

            // 将.env中的所有变量设置为系统属性
            for (Map.Entry<String, String> entry : envMap.entrySet()) {
                String key = entry.getKey();
                String value = entry.getValue();

                // 跳过已存在的系统环境变量，避免覆盖
                if (System.getenv(key) == null) {
                    System.setProperty(key, value);
                }
            }

            log.info(Messages.DOTENV_LOAD_SUCCESS, envMap.size());

        } catch (Exception e) {
            log.error(Messages.DOTENV_LOAD_FAIL + e.getMessage(), e);
        }
    }

    /**
     * 按候选路径顺序查找存在的.env文件
     *
     * @return 找到的.env文件，未找到返回 null
     */
    private static File findEnvFile() {
        for (String candidate : CANDIDATE_PATHS) {
            File file = new File(candidate);
            if (file.exists()) {
                return file;
            }
        }
        return null;
    }

    /**
     * 解析.env文件内容
     */
    private static Map<String, String> parseEnvFile(File file) throws Exception {
        Map<String, String> envMap = new HashMap<>();

        try (BufferedReader reader = new BufferedReader(new FileReader(file))) {
            String line;
            while ((line = reader.readLine()) != null) {
                line = line.trim();

                // 跳过空行和注释
                if (line.isEmpty() || line.startsWith("#")) {
                    continue;
                }

                // 解析 KEY=VALUE 格式
                if (line.contains("=")) {
                    int delimiter = line.indexOf("=");
                    String key = line.substring(0, delimiter).trim();
                    String value = line.substring(delimiter + 1).trim();

                    // 移除引号（如果有）
                    if ((value.startsWith("\"") && value.endsWith("\"")) ||
                        (value.startsWith("'") && value.endsWith("'"))) {
                        value = value.substring(1, value.length() - 1);
                    }

                    if (!key.isEmpty()) {
                        envMap.put(key, value);
                    }
                }
            }
        }

        return envMap;
    }

}

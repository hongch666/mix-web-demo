// @ts-check
import eslint from '@eslint/js';
import eslintPluginPrettierRecommended from 'eslint-plugin-prettier/recommended';
import globals from 'globals';
import tseslint from 'typescript-eslint';

export default tseslint.config(
  {
    // 配置自身、构建产物与覆盖率报告不参与检查
    ignores: ['eslint.config.mjs', 'dist/**', 'coverage/**'],
  },
  eslint.configs.recommended,
  ...tseslint.configs.recommendedTypeChecked,
  eslintPluginPrettierRecommended,
  {
    languageOptions: {
      globals: {
        ...globals.node,
        ...globals.jest,
      },
      sourceType: 'commonjs',
      parserOptions: {
        projectService: true,
        // @ts-ignore
        tsconfigRootDir: import.meta.dirname,
      },
    },
  },
  {
    rules: {
      // 格式化统一交给 Prettier（配置见 .prettierrc），此处只做校验不做修复
      'prettier/prettier': 'error',
      /*
       * 以下规则来自 recommendedTypeChecked，当前项目暂未满足，
       * 保留关闭状态并记录原因，后续可按文件粒度逐步开启：
       * - no-unsafe-*：TypeORM DataSource.query、Mongoose 聚合结果、Nacos SDK
       *   和 OpenAPI schema 遍历都会返回 any，需先补齐对应类型声明
       * - require-await：NestJS 中不少 async 方法是为保持对外接口签名一致而保留，
       *   去掉 async 会改变调用方契约
       */
      '@typescript-eslint/no-unsafe-assignment': 'off',
      '@typescript-eslint/no-unsafe-member-access': 'off',
      '@typescript-eslint/no-unsafe-call': 'off',
      '@typescript-eslint/no-unsafe-return': 'off',
      '@typescript-eslint/no-unsafe-argument': 'off',
      '@typescript-eslint/require-await': 'off',
    },
  },
  {
    // 环境声明文件用三斜线引用同目录的全局声明，是 .d.ts 的标准写法
    files: ['**/*.d.ts'],
    rules: {
      '@typescript-eslint/triple-slash-reference': 'off',
    },
  },
);

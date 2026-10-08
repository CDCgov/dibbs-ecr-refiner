import js from '@eslint/js';
import globals from 'globals';
import reactHooks from 'eslint-plugin-react-hooks';
import reactRefresh from 'eslint-plugin-react-refresh';
import tseslint from 'typescript-eslint';
import eslintConfigPrettier from 'eslint-config-prettier/flat';
import { importX } from 'eslint-plugin-import-x';
import { defineConfig } from 'eslint/config';
import eslintReact from '@eslint-react/eslint-plugin';
import testingLibraryPlugin from 'eslint-plugin-testing-library';
import tanstackQuery from '@tanstack/eslint-plugin-query';
import jsxA11yX from 'eslint-plugin-jsx-a11y-x';
import eslintReactKit from '@eslint-react/kit';
import { functionComponentDefinition } from './eslint-kit-rules/functionComponentDefinition.ts';
import stylistic from '@stylistic/eslint-plugin';

export default defineConfig(
  { ignores: ['dist', 'tests/setup.ts', 'src/api'] },
  {
    extends: [
      js.configs.recommended,
      eslintConfigPrettier,
      importX.flatConfigs.recommended,
      ...tseslint.configs.recommendedTypeChecked,
      eslintReactKit().use(functionComponentDefinition).getConfig(),
    ],
    files: ['**/*.{ts,tsx}'],
    languageOptions: {
      ecmaVersion: 2020,
      globals: globals.browser,
      parserOptions: {
        projectService: true,
        tsconfigRootDir: import.meta.dirname,
      },
    },
    plugins: {
      react: eslintReact,
      'react-hooks': reactHooks,
      'react-refresh': reactRefresh,
      '@tanstack/query': tanstackQuery,
      'jsx-a11y-x': jsxA11yX,
      '@stylistic': stylistic,
      'import-x': importX,
    },
    rules: {
      ...reactHooks.configs.recommended.rules,
      ...tanstackQuery.configs.recommended.rules,
      '@stylistic/jsx-self-closing-comp': [
        'error',
        {
          component: true,
          html: true,
        },
      ],
      '@stylistic/jsx-curly-brace-presence': [
        'error',
        {
          props: 'never',
          children: 'ignore',
        },
      ],

      'react-refresh/only-export-components': [
        'warn',
        { allowConstantExport: true },
      ],
      'import-x/extensions': ['error', 'never', { fix: true }],
      'no-restricted-imports': [
        'error',
        {
          paths: [
            {
              name: '@headlessui/react',
              importNames: ['MenuItems', 'ComboboxOptions'],
              message:
                'Use BaseMenuItems/BaseComboboxOptions from @/components/Dropdown instead for automatic z-index handling. See client/src/components/Dropdown/README.md',
            },
          ],
        },
      ],
      'no-console': ['error', { allow: ['warn', 'error'] }],
      '@typescript-eslint/no-floating-promises': 'error',
      '@typescript-eslint/no-unsafe-assignment': 'off',
      '@typescript-eslint/no-unsafe-call': 'off',
      '@typescript-eslint/no-unsafe-member-access': 'off',
      '@typescript-eslint/no-unsafe-return': 'off',
      '@typescript-eslint/no-unsafe-argument': 'off',
      '@typescript-eslint/no-misused-promises': 'off',
      '@typescript-eslint/no-redundant-type-constituents': 'off',
      '@typescript-eslint/no-explicit-any': 'error',
      '@typescript-eslint/consistent-type-definitions': ['error', 'interface'],
      '@typescript-eslint/no-restricted-types': [
        'error',
        {
          types: {
            'React.FC': {
              message:
                'Useless and has some drawbacks, see https://github.com/facebook/create-react-app/pull/8177',
            },
            'React.FunctionComponent': {
              message:
                'Useless and has some drawbacks, see https://github.com/facebook/create-react-app/pull/8177',
            },
            'React.FunctionalComponent': {
              message:
                'Preact specific, useless and has some drawbacks, see https://github.com/facebook/create-react-app/pull/8177',
            },
          },
        },
      ],
    },
    settings: {
      react: {
        version: 'detect',
      },
      'import-x/resolver': {
        typescript: {
          alwaysTryTypes: true,
          project: ['./tsconfig.app.json', './e2e/tsconfig.json'],
          noWarnOnMultipleProjects: true,
        },
        node: true, // or omit entirely if TypeScript resolves all imports
      },
    },
  },
  {
    files: ['src/**/*.{ts,tsx}'],
    rules: {
      'import-x/no-default-export': 'error',
    },
  },
  {
    // provide some flexibility for test files
    files: ['**/*.test.{ts,tsx}', '**/tests/**/*.ts'],
    plugins: { 'testing-library': testingLibraryPlugin },
    rules: {
      'testing-library/no-debugging-utils': 'error',
      '@typescript-eslint/no-explicit-any': 'off',
    },
  },
  {
    files: [
      'src/components/Dropdown/**/*.tsx',
      'src/components/Combobox/index.tsx',
    ],
    rules: {
      'no-restricted-imports': 'off',
    },
  },
  {
    files: [
      'playwright.config.{ts,tsx}',
      'e2e/**/*.spec.{ts,tsx}',
      'e2e/**/*.{ts,tsx}',
    ],
    rules: {
      'react-hooks/rules-of-hooks': 'off',
      'react-hooks/exhaustive-deps': 'off',
    },
  }
);

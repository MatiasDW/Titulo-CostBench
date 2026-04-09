import js from '@eslint/js'
import globals from 'globals'
import react from 'eslint-plugin-react'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
import { defineConfig, globalIgnores } from 'eslint/config'

export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{js,jsx}'],
    extends: [
      js.configs.recommended,
      reactHooks.configs.flat.recommended,
      reactRefresh.configs.vite,
    ],
    languageOptions: {
      ecmaVersion: 2020,
      globals: globals.browser,
      parserOptions: {
        ecmaVersion: 'latest',
        ecmaFeatures: { jsx: true },
        sourceType: 'module',
      },
    },
    plugins: {
      react,
    },
    settings: {
      react: {
        version: 'detect',
      },
    },
    rules: {
      // Needed so JSX usages like <motion.div /> and <Icon /> count as "used".
      'react/jsx-uses-vars': 'error',
      'react/jsx-uses-react': 'off',
      'no-unused-vars': [
        'error',
        { varsIgnorePattern: '^[A-Z_]', argsIgnorePattern: '^_' },
      ],

      // Keep hooks safety, relax compiler-oriented rules that are too strict for current codebase.
      'react-hooks/exhaustive-deps': 'warn',
      'react-hooks/immutability': 'off',
      'react-hooks/purity': 'off',
      'react-hooks/set-state-in-effect': 'warn',
      'react-hooks/use-memo': 'off',

      // Helpful in dev, but non-blocking while code is being refactored.
      'react-refresh/only-export-components': 'warn',
    },
  },
])

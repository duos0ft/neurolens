import js from "@eslint/js";
import { defineConfig } from "eslint/config";
import tseslint from "typescript-eslint";
import globals from "globals";
import reactHooks from "eslint-plugin-react-hooks";
import prettierRecommended from "eslint-plugin-prettier/recommended";
import stylistic from "@stylistic/eslint-plugin";

export default defineConfig([
    {
        ignores: ["node_modules/**", "dist/**", "storybook-static/**", "coverage/**"],
    },
    {
        files: ["**/*.{js,mjs,cjs,jsx,ts,tsx}"],
        extends: [js.configs.recommended, tseslint.configs.recommended],
    },
    {
        files: ["src/**/*.{js,jsx,ts,tsx}"],
        languageOptions: {
            globals: globals.browser,
        },
        plugins: {
            "react-hooks": reactHooks,
        },
        rules: {
            "react-hooks/rules-of-hooks": "error",
            "react-hooks/exhaustive-deps": "warn",
        },
    },
    {
        files: ["*.{js,mjs,cjs,ts}", ".storybook/**/*.{js,mjs,ts,tsx}"],
        languageOptions: {
            globals: globals.node,
        },
    },
    prettierRecommended,
    {
        files: ["**/*.{js,mjs,cjs,jsx,ts,tsx}"],
        plugins: {
            "@stylistic": stylistic,
        },
        rules: {
            "prettier/prettier": "off",
            "@stylistic/quotes": ["error", "double"],
            "@stylistic/jsx-quotes": ["error", "prefer-double"],
            "@stylistic/array-bracket-spacing": ["error", "always"],
            "@stylistic/object-curly-spacing": ["error", "always"],
        },
    },
]);

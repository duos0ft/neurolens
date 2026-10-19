import js from "@eslint/js";
import { defineConfig } from "eslint/config";
import tseslint from "typescript-eslint";
import globals from "globals";
import reactHooks from "eslint-plugin-react-hooks";
import stylistic from "@stylistic/eslint-plugin";

export default defineConfig([
    {
        ignores: [ "node_modules/**", "dist/**", "storybook-static/**", "coverage/**" ],
    },
    {
        files: [ "**/*.{js,mjs,cjs,jsx,ts,tsx}" ],
        extends: [ js.configs.recommended, tseslint.configs.recommended ],
    },
    {
        files: [ "src/**/*.{js,jsx,ts,tsx}" ],
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
        files: [ "*.{js,mjs,cjs,ts}", ".storybook/**/*.{js,mjs,ts,tsx}" ],
        languageOptions: {
            globals: globals.node,
        },
    },
    {
        files: [ "**/*.{js,mjs,cjs,jsx,ts,tsx}" ],
        plugins: {
            "@stylistic": stylistic,
        },
        rules: {
            "@stylistic/indent": [ "error", 4, { SwitchCase: 1 } ],
            "@stylistic/semi": [ "error", "always" ],
            "@stylistic/quotes": [ "error", "double", { avoidEscape: true } ],
            "@stylistic/jsx-quotes": [ "error", "prefer-double" ],
            "@stylistic/comma-dangle": [ "error", "always-multiline" ],
            "@stylistic/arrow-parens": [ "error", "always" ],
            "@stylistic/array-bracket-spacing": [ "error", "always" ],
            "@stylistic/object-curly-spacing": [ "error", "always" ],
            "@stylistic/comma-spacing": [ "error", { before: false, after: true } ],
            "@stylistic/key-spacing": [ "error", { beforeColon: false, afterColon: true } ],
            "@stylistic/space-infix-ops": "error",
            "@stylistic/space-before-blocks": "error",
            "@stylistic/space-in-parens": [ "error", "never" ],
            "@stylistic/eol-last": [ "error", "always" ],
            "@stylistic/no-multiple-empty-lines": [ "error", { max: 1, maxEOF: 0 } ],
        },
    },
]);

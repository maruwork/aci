// Baseline ESLint flat config bundled with ACI. Built-in core rules only (no
// plugins), so it lints any JavaScript without extra dependencies. A target
// repo's own eslint config takes precedence when present (see _eslint_command).
export default [
  {
    // Never lint generated, vendored, or minified output (e.g. Next.js build
    // chunks, webpack bundles). Linting build artifacts is meaningless, floods
    // the report, and can produce multi-megabyte output that fails to parse.
    ignores: [
      "**/node_modules/**",
      "**/dist/**",
      "**/build/**",
      "**/.next/**",
      "**/_next/**",
      "**/out/**",
      "**/coverage/**",
      "**/vendor/**",
      "**/*.min.js",
      "**/*-bundle.js",
      "**/*.bundle.js",
    ],
  },
  {
    rules: {
      "no-eval": "error",
      "no-implied-eval": "error",
      "no-new-func": "error",
      "no-debugger": "error",
      "no-unused-vars": "warn",
    },
  },
];

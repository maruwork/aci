// Baseline ESLint flat config bundled with ACI. Built-in core rules only (no
// plugins), so it lints any JavaScript without extra dependencies. A target
// repo's own eslint config takes precedence when present (see _eslint_command).
export default [
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

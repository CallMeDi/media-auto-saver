module.exports = {
  root: true,
  env: {
    node: true,
    browser: true,
  },
  extends: [
    'eslint:recommended',
    'plugin:vue/vue3-recommended',
  ],
  parserOptions: {
    ecmaVersion: 2020,
  },
  rules: {
    // Add any project-specific rules here
    'vue/multi-word-component-names': 'off', // Example: turn off for simple components
  },
  ignorePatterns: [
    "logs/",
    "*.log",
    "npm-debug.log*",
    "yarn-debug.log*",
    "yarn-error.log*",
    "pnpm-debug.log*",
    "lerna-debug.log*",
    "node_modules/",
    "dist/",
    "dist-ssr/",
    "*.local",
    ".vscode/",
    ".idea/",
    ".DS_Store",
    "*.suo",
    "*.ntvs*",
    "*.njsproj",
    "*.sln",
    "*.sw?",
  ],
};

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
};

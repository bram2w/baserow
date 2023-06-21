// Please keep in sync with the premium/enterprise eslintrc.js
module.exports = {
  root: true,
  env: {
    browser: true,
    node: true,
    jest: true,
    // required as jest uses jasmine's fail method
    // https://stackoverflow.com/questions/64413927/jest-eslint-fail-is-not-defined
    jasmine: true,
  },
  parserOptions: {
    parser: '@babel/eslint-parser',
    requireConfigFile: false,
  },
  extends: [
    '@nuxtjs',
    'plugin:nuxt/recommended',
    'plugin:prettier/recommended',
    'prettier',
  ],
  plugins: ['prettier', 'jest'],
  rules: {
    'no-console': 0,
    'vue/no-mutating-props': 0,
    'prettier/prettier': ['error'],
    'import/order': 'off',
    'vue/html-self-closing': 'off',
    'vue/no-unused-components': 'warn',
    'vue/no-use-computed-property-like-method': 'off',
    'vue/multi-word-component-names': 'off',
    'vue/no-reserved-component-names': 'off',
    'import/no-named-as-default-member': 'off',
  },
}

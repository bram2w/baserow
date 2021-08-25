// Allow to transform some ESM installed modules
const esModules = ['@nuxtjs/i18n'].join('|')

module.exports = {
  rootDir: '../../',
  testEnvironment: 'node',
  expand: true,
  forceExit: true,
  moduleNameMapper: {
    '^@baserow/(.*)$': '<rootDir>/$1',
    '^@/(.*)$': '<rootDir>/$1',
    '^~/(.*)$': '<rootDir>/$1',
    '^vue$': 'vue/dist/vue.common.js',
  },
  moduleFileExtensions: ['js', 'vue', 'json'],
  transform: {
    '^.+\\.js$': 'babel-jest',
    '.*\\.(vue)$': 'vue-jest',
  },
  transformIgnorePatterns: [`/node_modules/(?!${esModules})`],
  collectCoverage: true,
  collectCoverageFrom: [
    '<rootDir>/components/**/*.vue',
    '<rootDir>/pages/**/*.vue',
  ],
}

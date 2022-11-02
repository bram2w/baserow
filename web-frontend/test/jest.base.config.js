// Allow to transform some ESM installed modules
const esModules = ['@nuxtjs/i18n'].join('|')

module.exports = {
  rootDir: '../../../',
  testEnvironment: 'node',
  expand: true,
  forceExit: true,
  moduleNameMapper: {
    '^@baserow/(.*)$': '<rootDir>/web-frontend/$1',
    '^@/(.*)$': '<rootDir>/web-frontend/$1',
    '^~/(.*)$': '<rootDir>/web-frontend/$1',
    '^vue$': '<rootDir>/web-frontend/node_modules/vue/dist/vue.common.js',
  },
  moduleFileExtensions: ['js', 'vue', 'json'],
  transform: {
    '^.+\\.js$': 'babel-jest',
    '.*\\.(vue)$': '<rootDir>/web-frontend/node_modules/vue-jest',
    '^.+\\.svg$': '<rootDir>/web-frontend/test/helpers/stubSvgTransformer.js',
  },
  transformIgnorePatterns: [
    `<rootDir>/web-frontend/node_modules/(?!${esModules})`,
  ],
}

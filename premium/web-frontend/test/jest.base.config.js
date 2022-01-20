// Allow to transform some ESM installed modules
const esModules = ['@nuxtjs/i18n'].join('|')
module.exports = {
  rootDir: '../../../../',
  expand: true,
  forceExit: true,
  moduleDirectories: ['<rootDir>/web-frontend/node_modules/'],
  modulePaths: ['<rootDir>/web-frontend/node_modules/'],
  moduleNameMapper: {
    '^@baserow/(.*)$': '<rootDir>/web-frontend/$1',
    '^@baserow_premium/(.*)$':
      '<rootDir>/premium/web-frontend/modules/baserow_premium/$1',
    '^@/(.*)$': '<rootDir>/web-frontend/$1',
    '^~/(.*)$': '<rootDir>/web-frontend/$1',
    '^vue$': '<rootDir>/web-frontend/node_modules/vue/dist/vue.common.js',
  },
  moduleFileExtensions: ['js', 'vue', 'json'],
  transform: {
    '^.+\\.js$': 'babel-jest',
    '.*\\.(vue)$': '<rootDir>/web-frontend/node_modules/vue-jest',
  },
  transformIgnorePatterns: [
    `<rootDir>/web-frontend/node_modules/(?!(baserow|${esModules})/)`,
  ],
}

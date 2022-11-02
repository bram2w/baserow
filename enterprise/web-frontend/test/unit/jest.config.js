const baseConfig = require('../jest.base.config')

module.exports = Object.assign({}, baseConfig, {
  testEnvironment: 'jsdom',
  testMatch: ['<rootDir>/enterprise/web-frontend/test/unit/**/*.spec.js'],
  displayName: 'enterprise-unit',
  setupFilesAfterEnv: [
    '<rootDir>/enterprise/web-frontend/test/unit/jest.setup.js',
  ],
  snapshotSerializers: [
    '<rootDir>/web-frontend/node_modules/jest-serializer-vue',
  ],
})

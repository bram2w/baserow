const baseConfig = require('../jest.base.config')

module.exports = Object.assign({}, baseConfig, {
  testEnvironment: 'jsdom',
  testMatch: ['<rootDir>/premium/web-frontend/test/unit/**/*.spec.js'],
  displayName: 'premium-unit',
  setupFilesAfterEnv: [
    '<rootDir>/premium/web-frontend/test/unit/jest.setup.js',
  ],
  snapshotSerializers: [
    '<rootDir>/web-frontend/node_modules/jest-serializer-vue',
  ],
})

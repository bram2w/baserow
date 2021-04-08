const baseConfig = require('../jest.base.config')

module.exports = Object.assign({}, baseConfig, {
  testEnvironment: 'jsdom',
  testMatch: ['<rootDir>/test/unit/**/*.spec.js'],
  displayName: 'unit',
  setupFilesAfterEnv: ['./test/unit/jest.setup.js'],
})

const baseConfig = require('../jest.base.config')

module.exports = Object.assign({}, baseConfig, {
  testEnvironment: 'node',
  testMatch: ['<rootDir>/web-frontend/test/server/**/*.spec.js'],
  displayName: 'server',
  name: 'server',
  setupFilesAfterEnv: ['<rootDir>/web-frontend/test/server/jest.setup.js'],
})

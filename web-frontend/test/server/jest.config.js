const baseConfig = require('../jest.base.config')

module.exports = Object.assign({}, baseConfig, {
  testEnvironment: 'node',
  testMatch: ['<rootDir>/test/server/**/*.spec.js'],
  displayName: 'server',
  name: 'server',
  setupFilesAfterEnv: ['./test/server/jest.setup.js'],
})

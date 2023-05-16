const coverageConfig = require('./coverage.config.js')

module.exports = {
  testEnvironment: 'jsdom',
  testMatch: ['<rootDir>/test/unit/**/*.spec.js'],
  moduleFileExtensions: ['js', 'json', 'vue'],
  moduleNameMapper: {
    '^@baserow/(.*)$': '<rootDir>/$1',
    '^@/(.*)$': '<rootDir>/$1',
    '^~/(.*)$': '<rootDir>/$1',
    '^vue$': '<rootDir>/node_modules/vue/dist/vue.common.js',
  },
  transform: {
    '^.+\\.js$': 'babel-jest',
    '^.+\\.vue$': '@vue/vue2-jest',
    '^.+\\.svg$': '<rootDir>/test/helpers/stubSvgTransformer.js',
  },
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  snapshotSerializers: ['<rootDir>/node_modules/jest-serializer-vue'],
  ...coverageConfig,
}

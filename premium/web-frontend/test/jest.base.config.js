module.exports = {
  rootDir: require('path').resolve(__dirname, '..', '..', '..', 'web-frontend'),
  testEnvironment: 'node',
  expand: true,
  forceExit: true,
  moduleNameMapper: {
    '^@baserow/(.*)$': '<rootDir>$1',
    '^@baserow_premium/(.*)$':
      '<rootDir>/../premium/web-frontend/modules/baserow_premium/$1',
    '^@/(.*)$': '<rootDir>/$1',
    '^~/(.*)$': '<rootDir>/$1',
    '^vue$': 'vue/dist/vue.common.js',
  },
  moduleFileExtensions: ['js', 'vue', 'json'],
  transform: {
    '^.+\\.js$': 'babel-jest',
    '.*\\.(vue)$': 'vue-jest',
  },
  transformIgnorePatterns: ['node_modules/(?!(baserow)/)'],
  collectCoverage: true,
  collectCoverageFrom: [
    '<rootDir>/components/**/*.vue',
    '<rootDir>/pages/**/*.vue',
  ],
}

// Setting reporters on the command line does not work so enable via this env variable
// we have to set anyway when using the junit reporter in CI.
const junitReporterConfig = process.env.JEST_JUNIT_OUTPUT_DIR
  ? {
      reporters: ['default', '<rootDir>/web-frontend/node_modules/jest-junit'],
    }
  : {}
module.exports = {
  rootDir: '..',
  roots: ['<rootDir>/web-frontend/', '<rootDir>/premium/web-frontend'],
  moduleDirectories: ['<rootDir>/web-frontend/node_modules/'],
  modulePaths: ['<rootDir>/web-frontend/node_modules/'],
  projects: [
    '<rootDir>/web-frontend/test/unit',
    '<rootDir>/premium/web-frontend/test/unit',
    '<rootDir>/web-frontend/test/server',
  ],
  coverageReporters: [
    'html',
    'text-summary',
    ['cobertura', { projectRoot: '/baserow/' }],
  ],
  collectCoverageFrom: [
    '<rootDir>/premium/web-frontend/modules/**/*.{js,Vue,vue}',
    '<rootDir>/web-frontend/modules/**/*.{js,Vue,vue}',
    '!**/node_modules/**',
    '!**/.nuxt/**',
    '!**/reports/**',
    '!**/test/**',
    '!**/generated/**',
  ],
  ...junitReporterConfig,
}

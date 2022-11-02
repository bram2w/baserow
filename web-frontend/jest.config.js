// Setting reporters on the command line does not work so enable via this env variable
// we have to set anyway when using the junit reporter in CI.
const junitReporterConfig = process.env.JEST_JUNIT_OUTPUT_DIR
  ? {
      reporters: ['default', '<rootDir>/web-frontend/node_modules/jest-junit'],
    }
  : {}
module.exports = {
  // The rootDir used by jest must be the root of the repository so the
  // premium/enterprise tests and frontend code are contained within jest's rootDir.
  // This is because:
  // - Jest cannot collect coverage for files outside of its rootDir
  // - Jest struggles to run tests which are outside of its rootDir.
  rootDir: '..',
  roots: [
    '<rootDir>/web-frontend/',
    '<rootDir>/premium/web-frontend',
    '<rootDir>/enterprise/web-frontend',
  ],
  moduleDirectories: ['<rootDir>/web-frontend/node_modules/'],
  modulePaths: ['<rootDir>/web-frontend/node_modules/'],
  projects: [
    '<rootDir>/web-frontend/test/unit',
    '<rootDir>/premium/web-frontend/test/unit',
    '<rootDir>/enterprise/web-frontend/test/unit',
    '<rootDir>/web-frontend/test/server',
  ],
  coverageReporters: [
    'text-summary',
    ['cobertura', { projectRoot: '/baserow/' }],
  ],
  collectCoverageFrom: [
    '<rootDir>/premium/web-frontend/modules/**/*.{js,Vue,vue}',
    '<rootDir>/enterprise/web-frontend/modules/**/*.{js,Vue,vue}',
    '<rootDir>/web-frontend/modules/**/*.{js,Vue,vue}',
    '!**/node_modules/**',
    '!**/.nuxt/**',
    '!**/reports/**',
    '!**/test/**',
    '!**/generated/**',
  ],
  ...junitReporterConfig,
}

module.exports = {
  rootDir: '..',
  roots: ['<rootDir>/web-frontend/', '<rootDir>/premium/web-frontend'],
  moduleDirectories: ['<rootDir>/web-frontend/node_modules/'],
  modulePaths: ['<rootDir>/web-frontend/node_modules/'],
  projects: ['test/server', 'test/unit', '../premium/web-frontend/test/unit'],
  // reporters: ['default', '<rootDir>/web-frontend/node_modules/jest-junit'],
  reporters: ['default', '<rootDir>/web-frontend/node_modules/jest-junit'],
  coverageReporters: [
    'html',
    'text',
    'text-summary',
    ['cobertura', { projectRoot: '/baserow/' }],
  ],
  collectCoverageFrom: [
    '**/*.{js,Vue,vue}',
    '!**/node_modules/**',
    '!**/.nuxt/**',
    '!**/reports/**',
    '!**/test/**',
    '!**/generated/**',
  ],
}

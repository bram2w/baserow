module.exports = {
  projects: ['test/server', 'test/unit', '../premium/web-frontend/test/unit'],
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

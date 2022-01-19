module.exports = {
  projects: ['test/server', 'test/unit', '../premium/web-frontend/test/unit'],
  coverageReporters: [
    'html',
    'text-summary',
    ['cobertura', { projectRoot: '/baserow/' }],
  ],
}

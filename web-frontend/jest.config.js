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
}

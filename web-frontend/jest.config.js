// The main jest config file used to run all of our tests.
module.exports = {
  // The rootDir used by jest must be the root of the repository so the premium tests
  // and frontend code are contained within jest's rootDir. This is because:
  // - Jest cannot collect coverage for files outside of its rootDir
  // - Jest struggles to run tests which are outside of its rootDir.
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

/**
 * This file can be used in combination with intellij idea so the @baserow path
 * resolves.
 *
 * Intellij IDEA: Preferences -> Languages & Frameworks -> JavaScript -> Webpack ->
 * webpack configuration file
 */

const path = require('path')

module.exports = {
  resolve: {
    extensions: ['.js', '.json', '.vue', '.ts'],
    root: path.resolve(__dirname),
    alias: {
      '@baserow': path.resolve(__dirname),
      '@baserow_premium': path.resolve(
        __dirname,
        '../premium/web-frontend/modules/baserow_premium'
      ),
      '@baserow_premium_test': path.resolve(
        __dirname,
        '../premium/web-frontend/test'
      ),
      '@baserow_enterprise': path.resolve(
        __dirname,
        '../enterprise/web-frontend/modules/baserow_enterprise'
      ),
      '@baserow_enterprise_test': path.resolve(
        __dirname,
        '../enterprise/web-frontend/test'
      ),
      '@baserow_test_cases': path.resolve(__dirname, '../tests/cases'),
    },
  },
}

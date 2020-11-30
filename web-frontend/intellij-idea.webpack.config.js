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
    },
  },
}

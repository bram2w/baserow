/**
 * This file can be used in combination with intellij idea so the @baserow path
 * resolves.
 */

const path = require('path')

module.exports = {
  resolve: {
    extensions: ['.js', '.json', '.vue', '.ts'],
    root: path.resolve(__dirname),
    alias: {
      '@baserow': path.resolve(__dirname)
    }
  }
}

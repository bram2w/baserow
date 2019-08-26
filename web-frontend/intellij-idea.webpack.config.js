/** This file can be used in combination with intellij idea so the @ path resolves **/

const path = require('path')

module.exports = {
  resolve: {
    extensions: ['.js', '.json', '.vue', '.ts'],
    root: path.resolve(__dirname),
    alias: {
      '@': path.resolve(__dirname),
      '@@': path.resolve(__dirname),
      '~': path.resolve(__dirname),
      '~~': path.resolve(__dirname)
    }
  }
}

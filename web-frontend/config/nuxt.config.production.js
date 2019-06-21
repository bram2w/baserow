import path from 'path'

import base from './nuxt.config.base.js'

export default function(rootDir) {
  const merge = require(rootDir + '/node_modules/lodash.merge')

  /**
   * Because the nuxt source files are located in we web-frontend directory, but
   * the project is started from another directory we have to explicitly set the
   * source directory which contains the nuxt files and the root directory which
   * contains the node modules.
   */
  const config = {
    rootDir: rootDir,
    srcDir: path.resolve(__dirname, '../')
  }

  return merge(base, config)
}

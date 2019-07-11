import { resolve } from 'path'
import _ from 'lodash'

import base from './nuxt.config.base.js'

const config = {
  rootDir: resolve(__dirname, '../'),
  css: [],
  dev: false,
  debug: false,
  env: {
    // The API base url, this will be prepended to the urls of the remote calls.
    baseUrl: 'http://localhost/api/v0'
  }
}

export default _.assign({}, base, config)

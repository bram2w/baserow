import { resolve } from 'path'
import _ from 'lodash'

import base from './nuxt.config.base.js'

export default _.assign({}, base(), {
  rootDir: resolve(__dirname, '../'),
  css: [],
  dev: false,
  debug: false,
  env: {
    // The API base url, this will be prepended to the urls of the remote calls.
    baseUrl: 'http://localhost/api/v0',
  },
})

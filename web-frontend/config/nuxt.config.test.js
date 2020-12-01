import { resolve } from 'path'
import _ from 'lodash'

import base from './nuxt.config.base.js'

export default _.assign({}, base(), {
  rootDir: resolve(__dirname, '../'),
  css: [],
  dev: false,
  debug: false,
  env: {
    PRIVATE_BACKEND_URL: 'http://localhost',
    PUBLIC_BACKEND_URL: 'http://localhost',
    PUBLIC_WEB_FRONTEND_URL: 'http://localhost',
    INITIAL_TABLE_DATA_LIMIT: null,
  },
})

import _ from 'lodash'
import base from 'baserow/config/nuxt.config.base.js'

const config = {
  env: {
    baseUrl: 'http://sandbox:8000/api/v0',
    publicBaseUrl: 'http://localhost:8001/api/v0',
  },
}

export default _.assign(base('baserow'), config)

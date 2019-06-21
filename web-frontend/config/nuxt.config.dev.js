import merge from 'lodash.merge'
import StyleLintPlugin from 'stylelint-webpack-plugin'

import base from './nuxt.config.base.js'

const config = {
  build: {
    extend(config, ctx) {
      // Run ESLint ad Stylelint on save
      if (ctx.isDev && ctx.isClient) {
        config.module.rules.push({
          enforce: 'pre',
          test: /\.(js|vue)$/,
          loader: 'eslint-loader',
          exclude: /(node_modules)/
        })
      }
    },

    plugins: [
      new StyleLintPlugin({
        syntax: 'scss'
      })
    ]
  }
}

export default merge(base, config)

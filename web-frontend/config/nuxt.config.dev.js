import StyleLintPlugin from 'stylelint-webpack-plugin'

import base from './nuxt.config.base.js'

export default Object.assign(base(), {
  vue: {
    config: {
      productionTip: false,
      devtools: true,
      performance: true,
      silent: false,
    },
  },
  dev: true,
  build: {
    extend(config, ctx) {
      if (ctx.isDev && ctx.isClient) {
        config.module.rules.push({
          enforce: 'pre',
          test: /\.(js|vue)$/,
          loader: 'eslint-loader',
          exclude: /(node_modules)/,
        })
      }
      config.node = { fs: 'empty' }
    },
    babel: { compact: true },
    plugins: [
      new StyleLintPlugin({
        syntax: 'scss',
      }),
    ],
  },
})

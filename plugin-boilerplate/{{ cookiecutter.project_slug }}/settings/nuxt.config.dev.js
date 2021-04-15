import StyleLintPlugin from 'stylelint-webpack-plugin'

import baseConfig from './nuxt.config.base'

export default Object.assign(baseConfig, {
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
    },

    plugins: [
      new StyleLintPlugin({
        syntax: 'scss',
      }),
    ],
  },
})

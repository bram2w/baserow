import StyleLintPlugin from 'stylelint-webpack-plugin'

import baseConfig from './nuxt.config.base'

export default Object.assign(baseConfig, {
  build: {
    plugins: [
      new StyleLintPlugin({
        syntax: 'scss',
      }),
    ],
  },
})

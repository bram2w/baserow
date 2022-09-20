import path from 'path'

import { routes } from './routes'

import en from './locales/en.json'
import fr from './locales/fr.json'

export default function () {
  this.nuxt.hook('i18n:extend-messages', (additionalMessages) => {
    additionalMessages.push({ en, fr })
  })

  // Register new alias to the web-frontend directory.
  this.options.alias['@baserow_enterprise'] = path.resolve(__dirname, './')

  // Remove the existing index route and add our own routes.
  this.extendRoutes((configRoutes) => {
    configRoutes.push(...routes)
  })

  this.appendPlugin({
    src: path.resolve(__dirname, 'plugin.js'),
  })

  // Override Baserow's existing default.scss in favor of our own because that one
  // imports the original. We do this so that we can use the existing variables,
  // mixins, placeholders etc.
  this.options.css[0] = path.resolve(__dirname, 'assets/scss/default.scss')
}

import path from 'path'

import { routes } from './routes'
import en from './locales/en.json'
import fr from './locales/fr.json'

export default function DatabaseModule(options) {
  this.addPlugin({ src: path.resolve(__dirname, 'middleware.js') })

  // Add the plugin to register the database application.
  this.appendPlugin({
    src: path.resolve(__dirname, 'plugin.js'),
  })

  // Add all the related routes.
  this.extendRoutes((configRoutes) => {
    configRoutes.push(...routes)
  })

  this.nuxt.hook('i18n:extend-messages', function (additionalMessages) {
    additionalMessages.push({ en, fr })
  })
}

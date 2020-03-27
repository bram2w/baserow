import path from 'path'

import { routes } from './routes'

export default function DatabaseModule(options) {
  // Add the plugin to register the database application.
  this.appendPlugin({
    src: path.resolve(__dirname, 'plugin.js')
  })

  // Add all the related routes.
  this.extendRoutes(configRoutes => {
    configRoutes.push(...routes)
  })
}

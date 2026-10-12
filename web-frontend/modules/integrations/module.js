import {
  defineNuxtModule,
  addPlugin,
  createResolver,
  extendPages,
} from 'nuxt/kit'
import { locales } from '../../config/locales.js'
import { routes as oauth2Routes } from './oauth2/routes.js'

export default defineNuxtModule({
  meta: {
    name: 'integrations-module',
  },

  setup(options, nuxt) {
    const { resolve } = createResolver(import.meta.url)

    // Register main plugin
    addPlugin({
      src: resolve('./plugin.js'),
    })
    addPlugin({
      src: resolve('./oauth2/plugins/oauth2Result.js'),
      mode: 'client',
    })

    extendPages((pages) => {
      pages.push(...oauth2Routes)
    })

    nuxt.hook('i18n:registerModule', (register) => {
      register({
        langDir: resolve('./locales'),
        locales,
      })
    })
  },
})

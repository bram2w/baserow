import path from 'path'
import _ from 'lodash'
import serveStatic from 'serve-static'

import { routes } from './routes'
import head from './head'
import en from './locales/en.json'
import fr from './locales/fr.json'
import nl from './locales/nl.json'
import de from './locales/de.json'
import es from './locales/es.json'
import it from './locales/it.json'

export default function CoreModule(options) {
  /**
   * This function adds a plugin, but rather then prepending it to the list it will
   * be appended.
   */
  this.appendPlugin = (template) => {
    this.addPlugin(template)
    this.options.plugins.push(this.options.plugins.splice(0, 1)[0])
  }

  // Baserow must be run in universal mode.
  this.options.mode = 'universal'

  // Set the default head object, but override the configured head.
  // @TODO if a child is a list the new children must be appended instead of overridden.
  this.options.head = _.merge({}, head, this.options.head)

  // Store must be true in order for the store to be injected into the context.
  this.options.store = true

  // Register new alias to the web-frontend directory.
  this.options.alias['@baserow'] = path.resolve(__dirname, '../../')

  const BASEROW_PUBLIC_URL = process.env.BASEROW_PUBLIC_URL
  if (BASEROW_PUBLIC_URL) {
    process.env.PUBLIC_BACKEND_URL = BASEROW_PUBLIC_URL
    process.env.PUBLIC_WEB_FRONTEND_URL = BASEROW_PUBLIC_URL
  }

  // The core depends on these modules.
  this.requireModule('cookie-universal-nuxt')
  this.requireModule([
    'nuxt-env',
    {
      keys: [
        {
          key: 'PRIVATE_BACKEND_URL',
          default: 'http://backend:8000',
        },
        {
          key: 'BASEROW_DISABLE_PUBLIC_URL_CHECK',
          default: false,
        },
        {
          key: 'PUBLIC_BACKEND_URL',
          default: 'http://localhost:8000',
        },
        {
          key: 'PUBLIC_WEB_FRONTEND_URL',
          default: 'http://localhost:3000',
        },
        {
          key: 'INITIAL_TABLE_DATA_LIMIT',
          default: null,
        },
        {
          // Set to `1` to force download links to download files via XHR query
          // to bypass `Content-Disposition: inline` that can't be overridden
          // in another way.
          // If your files are stored under another origin, you also
          // must add CORS headers to your server.
          key: 'DOWNLOAD_FILE_VIA_XHR',
          default: false,
        },
        {
          // If you change this default please also update the default for the
          // backend found in src/baserow/config/settings/base.py:321
          key: 'HOURS_UNTIL_TRASH_PERMANENTLY_DELETED',
          default: 24 * 3,
        },
        {
          key: 'DISABLE_ANONYMOUS_PUBLIC_VIEW_WS_CONNECTIONS',
          default: false,
        },
        {
          key: 'BASEROW_MAX_IMPORT_FILE_SIZE_MB',
          default: 512, // 512Mb
        },
        {
          key: 'FEATURE_FLAGS',
          default: '',
        },
        {
          key: 'BASEROW_DISABLE_GOOGLE_DOCS_FILE_PREVIEW',
          default: '',
        },
        {
          key: 'BASEROW_MAX_SNAPSHOTS_PER_GROUP',
          default: -1,
        },
      ],
    },
  ])

  const locales = [
    { code: 'en', name: 'English', file: 'en.json' },
    { code: 'fr', name: 'Français', file: 'fr.json' },
    { code: 'nl', name: 'Nederlands', file: 'nl.json' },
    { code: 'de', name: 'Deutsch', file: 'de.json' },
    { code: 'es', name: 'Español (Beta)', file: 'es.json' },
    { code: 'it', name: 'Italiano (Beta)', file: 'it.json' },
  ]

  this.requireModule([
    '@nuxtjs/i18n',
    {
      strategy: 'no_prefix',
      defaultLocale: 'en',
      detectBrowserLanguage: {
        useCookie: true,
        cookieKey: 'i18n-language',
      },
      locales,
      langDir: path.resolve(__dirname, '../../locales/'),
      vueI18n: {
        fallbackLocale: 'en',
        silentFallbackWarn: true,
      },
    },
  ])

  this.nuxt.hook('i18n:extend-messages', function (additionalMessages) {
    additionalMessages.push({ en, fr, nl, de, es, it })
  })

  // Serve the static directory
  // @TODO we might need to change some things here for production. (See:
  //  https://github.com/nuxt/nuxt.js/blob/5a6cde3ebc23f04e89c30a4196a9b7d116b6d675/
  //  packages/server/src/server.js)
  const staticMiddleware = serveStatic(
    path.resolve(__dirname, 'static'),
    this.options.render.static
  )
  this.addServerMiddleware(staticMiddleware)

  this.addLayout(path.resolve(__dirname, 'layouts/error.vue'), 'error')
  this.addLayout(path.resolve(__dirname, 'layouts/app.vue'), 'app')
  this.addLayout(path.resolve(__dirname, 'layouts/login.vue'), 'login')

  this.addPlugin({ src: path.resolve(__dirname, 'plugins/global.js') })
  this.addPlugin({ src: path.resolve(__dirname, 'plugins/vuelidate.js') })
  this.addPlugin({
    src: path.resolve(__dirname, 'plugins/vueDatepicker.js'),
    ssr: false,
  })
  this.addPlugin({ src: path.resolve(__dirname, 'middleware.js') })

  // Some plugins depends on i18n instance so the plugin must be added
  // after the nuxt-i18n module's plugin
  this.appendPlugin({ src: path.resolve(__dirname, 'plugin.js') })

  // This plugin must be added after nuxt-i18n module's plugin
  this.appendPlugin({ src: path.resolve(__dirname, 'plugins/i18n.js') })

  // The client handler depends on environment variables so the plugin must be added
  // after the nuxt-env module's plugin.
  this.appendPlugin({
    src: path.resolve(__dirname, 'plugins/clientHandler.js'),
  })
  this.appendPlugin({
    src: path.resolve(__dirname, 'plugins/realTimeHandler.js'),
  })
  this.appendPlugin({ src: path.resolve(__dirname, 'plugins/auth.js') })
  this.appendPlugin({ src: path.resolve(__dirname, 'plugins/featureFlags.js') })
  this.appendPlugin({ src: path.resolve(__dirname, 'plugins/papa.js') })
  this.appendPlugin({ src: path.resolve(__dirname, 'plugins/ensureRender.js') })

  this.extendRoutes((configRoutes) => {
    // Remove all the routes created by nuxt.
    let i = configRoutes.length
    while (i--) {
      if (configRoutes[i].component.includes('/@nuxt/')) {
        configRoutes.splice(i, 1)
      }
    }

    // Add the routes from the ./routes.js.
    configRoutes.push(...routes)
  })

  // Add a default authentication middleware. In order to add a new middleware the
  // middleware.js file has to be changed.
  this.options.router.middleware.push('authentication')

  // Add the main scss file which contains all the generic scss code.
  this.options.css.push(path.resolve(__dirname, 'assets/scss/default.scss'))
}

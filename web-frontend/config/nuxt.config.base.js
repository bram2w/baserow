export default {
  mode: 'universal',

  /*
   ** Headers of the page
   */
  head: {
    title: 'Baserow',
    meta: [
      { charset: 'utf-8' },
      { name: 'viewport', content: 'width=device-width, initial-scale=1' }
    ]
  },

  /*
   ** Customize the progress-bar color
   */
  loading: { color: '#fff' },

  /*
   ** Global CSS
   */
  css: ['@/assets/scss/default.scss'],

  /*
   ** Plugins to load before mounting the App
   */
  plugins: [{ src: '@/plugins/auth.js' }, { src: '@/plugins/vuelidate.js' }],

  /*
   ** Nuxt.js modules
   */
  modules: ['@nuxtjs/axios', 'cookie-universal-nuxt'],

  router: {
    middleware: 'authentication'
  },

  env: {
    // The API base url, this will be prepended to the urls of the remote calls.
    baseUrl: 'http://localhost:8000/api/v0'
  }
}

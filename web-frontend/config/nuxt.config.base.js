export default {
  modules: ['@/modules/core/module.js', '@/modules/database/module.js'],

  env: {
    // The API base url, this will be prepended to the urls of the remote calls.
    baseUrl: 'http://backend:8000/api/v0',

    // If the API base url must different at the client side it can be changed
    // here.
    publicBaseUrl: 'http://localhost:8000/api/v0',
  },
}

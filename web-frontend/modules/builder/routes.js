import path from 'path'

export const routes = [
  {
    name: 'builder-page',
    path: '/builder/:builderId/page/:pageId',
    component: path.resolve(__dirname, 'pages/pageEditor.vue'),
    props(route) {
      const p = { ...route.params }
      p.builderId = parseInt(p.builderId)
      p.pageId = parseInt(p.pageId)
      return p
    },
  },
  {
    name: 'application-builder-page',
    path: '*',
    component: path.resolve(__dirname, 'pages/publicPage.vue'),
    // If publishedBuilderRoute is true, then that route will only be used on a
    // different subdomain.
    meta: { publishedBuilderRoute: true },
  },
  {
    name: 'health-check',
    path: '/_health',
    component: path.resolve(__dirname, '../core/pages/_health.vue'),
    meta: { publishedBuilderRoute: true },
  },
  {
    name: 'application-builder-page',
    // This route to the preview of the builder page
    path: '/builder/:builderId/preview*',
    component: path.resolve(__dirname, 'pages/publicPage.vue'),
  },
]

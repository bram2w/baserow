import path from 'path'

export const routes = [
  {
    name: 'tmp-app-builder-page',
    path: '/tmp-app-builder-page',
    component: path.resolve(__dirname, 'pages/tmpPageBuilder.vue'),
  },
  {
    name: 'application-builder-page',
    path: '*',
    component: path.resolve(__dirname, 'pages/publishedWebsitePage.vue'),
    // If publishedWebsiteRoute is true, then that route will only be used on a
    // different subdomain.
    meta: { publishedWebsiteRoute: true },
  },
  {
    name: 'application-builder-page',
    // This route to the preview of the website
    path: '/preview/application/:id/page*',
    component: path.resolve(__dirname, 'pages/previewWebsitePage.vue'),
  },
]

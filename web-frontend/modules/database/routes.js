import path from 'path'

export const routes = [
  {
    name: 'database-table',
    path: '/database/:databaseId/table/:tableId/:viewId?',
    component: path.resolve(__dirname, 'pages/table.vue'),
    props(route) {
      // @TODO figure out why the route param is empty on the server side.
      const p = { ...route.params }
      p.databaseId = parseInt(p.databaseId)
      p.tableId = parseInt(p.tableId)
      p.viewId = p.viewId ? parseInt(p.viewId) : null
      return p
    },
  },
  {
    name: 'database-api-docs',
    path: '/api/docs',
    component: path.resolve(__dirname, 'pages/APIDocs.vue'),
  },
  {
    name: 'database-api-docs-detail',
    path: '/api/docs/database/:databaseId',
    component: path.resolve(__dirname, 'pages/APIDocsDatabase.vue'),
  },
  {
    name: 'database-table-form',
    path: '/form/:slug',
    component: path.resolve(__dirname, 'pages/form.vue'),
  },
]

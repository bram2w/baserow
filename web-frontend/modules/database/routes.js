import path from 'path'

export const databaseRoutes = [
  {
    name: 'database-table',
    path: '/database/:databaseId/table/:tableId/:viewId?',
    component: path.resolve(__dirname, 'pages/Table.vue'),
    props(route) {
      // @TODO figure out why the route param is empty on the server side.
      const p = { ...route.params }
      p.databaseId = parseInt(p.databaseId)
      p.tableId = parseInt(p.tableId)
      p.viewId = p.viewId ? parseInt(p.viewId) : null
      return p
    }
  }
]

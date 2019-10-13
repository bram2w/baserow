import path from 'path'

export const databaseRoutes = [
  {
    name: 'application-database',
    path: '/database/:id',
    component: path.resolve(__dirname, 'pages/Database.vue'),
    props(route) {
      const props = { ...route.params }
      props.id = parseInt(props.id)
      return props
    }
  }
]

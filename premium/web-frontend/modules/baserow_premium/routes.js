// import path from 'path'

import path from 'path'

export const routes = [
  {
    name: 'admin-users',
    path: '/admin/users',
    component: path.resolve(__dirname, 'pages/admin/userAdmin.vue'),
  },
]

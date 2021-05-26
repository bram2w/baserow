import path from 'path'

export const routes = [
  {
    name: 'admin-dashboard',
    path: '/admin/dashboard',
    component: path.resolve(__dirname, 'pages/admin/dashboard.vue'),
  },
  {
    name: 'admin-users',
    path: '/admin/users',
    component: path.resolve(__dirname, 'pages/admin/userAdmin.vue'),
  },
]

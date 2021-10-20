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
    component: path.resolve(__dirname, 'pages/admin/users.vue'),
  },
  {
    name: 'admin-groups',
    path: '/admin/groups',
    component: path.resolve(__dirname, 'pages/admin/groups.vue'),
  },
  {
    name: 'admin-licenses',
    path: '/admin/licenses',
    component: path.resolve(__dirname, 'pages/admin/licenses.vue'),
  },
  {
    name: 'admin-license',
    path: '/admin/license/:id',
    component: path.resolve(__dirname, 'pages/admin/license.vue'),
  },
]

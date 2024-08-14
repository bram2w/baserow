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
    name: 'admin-workspaces',
    path: '/admin/workspaces',
    component: path.resolve(__dirname, 'pages/admin/workspaces.vue'),
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
  {
    name: 'database-public-kanban-view',
    path: '/public/kanban/:slug',
    component: '@baserow/modules/database/pages/publicView.vue',
  },
  {
    name: 'database-public-calendar-view',
    path: '/public/calendar/:slug',
    component: '@baserow/modules/database/pages/publicView.vue',
  },
]

import path from 'path'

export const routes = [
  {
    name: 'dashboard-application',
    path: '/dashboard/:dashboardId',
    file: path.resolve(__dirname, 'pages/dashboard.vue'),
  },
  {
    name: 'dashboard-public',
    path: '/public/dashboard/:slug',
    file: path.resolve(__dirname, 'pages/publicDashboard.vue'),
  },
]

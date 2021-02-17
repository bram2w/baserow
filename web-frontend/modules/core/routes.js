import path from 'path'

export const routes = [
  {
    name: 'index',
    path: '',
    component: path.resolve(__dirname, 'pages/index.vue'),
  },
  {
    name: 'login',
    path: '/login',
    component: path.resolve(__dirname, 'pages/login.vue'),
  },
  {
    name: 'signup',
    path: '/signup',
    component: path.resolve(__dirname, 'pages/signup.vue'),
  },
  {
    name: 'forgot-password',
    path: '/forgot-password',
    component: path.resolve(__dirname, 'pages/forgotPassword.vue'),
  },
  {
    name: 'reset-password',
    path: '/reset-password/:token',
    component: path.resolve(__dirname, 'pages/resetPassword.vue'),
  },
  {
    name: 'dashboard',
    path: '/dashboard',
    component: path.resolve(__dirname, 'pages/dashboard.vue'),
  },
  {
    name: 'group-invitation',
    path: '/group-invitation/:token',
    component: path.resolve(__dirname, 'pages/groupInvitation.vue'),
  },
  {
    name: 'admin-settings',
    path: '/admin/settings',
    component: path.resolve(__dirname, 'pages/admin/settings.vue'),
  },
  {
    name: 'style-guide',
    path: '/style-guide',
    component: path.resolve(__dirname, 'pages/styleGuide.vue'),
  },
  {
    name: 'health-check',
    path: '/_health',
    component: path.resolve(__dirname, 'pages/_health.vue'),
  },
]

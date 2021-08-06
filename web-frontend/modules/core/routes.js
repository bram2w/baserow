import path from 'path'

// Note that routes can't start with `/api/`, `/ws/` or `/media/` because they are
// reserved for the backend. In some cases, for example with the Heroku or Clouron
// deployment, the Baserow installation will share a single domain and port and then
// those URLS are forwarded to the backend or media files server. The rest is
// forwarded to the web-frontend.
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

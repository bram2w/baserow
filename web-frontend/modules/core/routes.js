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
    name: 'dashboard',
    path: '/dashboard',
    component: path.resolve(__dirname, 'pages/dashboard.vue'),
  },
  {
    name: 'style-guide',
    path: '/style-guide',
    component: path.resolve(__dirname, 'pages/style-guide.vue'),
  },
  {
    name: 'health-check',
    path: '/_health',
    component: path.resolve(__dirname, 'pages/_health.vue'),
  },
]

import path from 'path'

export const routes = [
  {
    name: 'enterprise-test',
    path: '/enterprise/test',
    component: path.resolve(__dirname, 'pages/test.vue'),
  },
]

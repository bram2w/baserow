import path from 'path'

export const routes = [
  {
    name: 'login-saml',
    path: '/login/saml',
    component: path.resolve(__dirname, 'pages/login/loginWithSAML.vue'),
  },
  {
    name: 'login-error',
    path: '/login/error',
    component: path.resolve(__dirname, 'pages/login/loginError.vue'),
  },
  {
    name: 'admin-auth-providers',
    path: '/admin/auth-providers',
    component: path.resolve(__dirname, 'pages/admin/authProviders.vue'),
  },
  {
    name: 'admin-audit-log',
    path: '/admin/audit-log',
    component: path.resolve(__dirname, 'pages/auditLog.vue'),
  },
  {
    name: 'workspace-audit-log',
    path: '/workspace/:workspaceId/audit-log',
    component: path.resolve(__dirname, 'pages/auditLog.vue'),
  },
]

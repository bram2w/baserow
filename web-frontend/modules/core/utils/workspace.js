import { isSecureURL } from '@baserow/modules/core/utils/string'

// NOTE: this has been deliberately left as `group`. A future task will rename it.
const cookieWorkspaceName = 'baserow_group_id'

export const setWorkspaceCookie = (workspaceId, { $cookies, $config }) => {
  if (process.SERVER_BUILD) return
  const secure = isSecureURL($config.PUBLIC_WEB_FRONTEND_URL)
  $cookies.set(cookieWorkspaceName, workspaceId, {
    path: '/',
    maxAge: 60 * 60 * 24 * 7,
    sameSite: $config.BASEROW_FRONTEND_SAME_SITE_COOKIE,
    secure,
  })
}

export const unsetWorkspaceCookie = ({ $cookies }) => {
  if (process.SERVER_BUILD) return
  $cookies.remove(cookieWorkspaceName)
}

export const getWorkspaceCookie = ({ $cookies }) => {
  if (process.SERVER_BUILD) return
  return $cookies.get(cookieWorkspaceName)
}

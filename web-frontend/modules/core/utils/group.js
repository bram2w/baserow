import { isSecureURL } from '@baserow/modules/core/utils/string'

const cookieGroupName = 'baserow_group_id'

export const setGroupCookie = (groupId, { $cookies, $env }) => {
  if (process.SERVER_BUILD) return
  const secure = isSecureURL($env.PUBLIC_WEB_FRONTEND_URL)
  $cookies.set(cookieGroupName, groupId, {
    path: '/',
    maxAge: 60 * 60 * 24 * 7,
    sameSite: 'lax',
    secure,
  })
}

export const unsetGroupCookie = ({ $cookies }) => {
  if (process.SERVER_BUILD) return
  $cookies.remove(cookieGroupName)
}

export const getGroupCookie = ({ $cookies }) => {
  if (process.SERVER_BUILD) return
  return $cookies.get(cookieGroupName)
}

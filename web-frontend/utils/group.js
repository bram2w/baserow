const cookieGroupName = 'baserow_group_id'

export const setGroupCookie = (groupId, cookie) => {
  if (process.SERVER_BUILD) return
  cookie.set(cookieGroupName, groupId)
}

export const unsetGroupCookie = cookie => {
  if (process.SERVER_BUILD) return
  cookie.remove(cookieGroupName)
}

export const getGroupCookie = cookie => {
  if (process.SERVER_BUILD) return
  return cookie.get(cookieGroupName)
}

export function aUser({
  id = 1,
  username = 'user@baserow.io',
  name = 'user_name',
  workspaces = [
    {
      id: 1,
      name: 'some_workspace',
      permissions: 'ADMIN',
    },
  ],
  lastLogin = '2021-04-26T07:50:45.643059Z',
  dateJoined = '2021-04-21T12:04:27.379781Z',
  isActive = true,
  isStaff = true,
}) {
  return {
    id,
    username,
    name,
    workspaces,
    last_login: lastLogin,
    date_joined: dateJoined,
    is_active: isActive,
    is_staff: isStaff,
  }
}

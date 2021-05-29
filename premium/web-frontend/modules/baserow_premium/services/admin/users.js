import baseService from '@baserow_premium/crud_table/baseService'

export default (client) => {
  return Object.assign(baseService(client, '/admin/users/'), {
    update(userId, values) {
      return client.patch(`/admin/users/${userId}/`, values)
    },
    delete(userId) {
      return client.delete(`/admin/users/${userId}/`)
    },
  })
}

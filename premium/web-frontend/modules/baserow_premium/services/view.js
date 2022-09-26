export default (client) => {
  return {
    update(viewId, values) {
      return client.patch(`/database/view/${viewId}/premium`, values)
    },
  }
}

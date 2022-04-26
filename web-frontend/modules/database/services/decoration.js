export default (client) => {
  return {
    fetchAll(viewId) {
      return client.get(`/database/views/${viewId}/decoration/`)
    },
    create(viewId, values) {
      return client.post(`/database/views/${viewId}/decorations/`, values)
    },
    get(viewDecorationId) {
      return client.get(`/database/views/decoration/${viewDecorationId}/`)
    },
    update(viewDecorationId, values) {
      return client.patch(
        `/database/views/decoration/${viewDecorationId}/`,
        values
      )
    },
    delete(viewDecorationId) {
      return client.delete(`/database/views/decoration/${viewDecorationId}/`)
    },
  }
}

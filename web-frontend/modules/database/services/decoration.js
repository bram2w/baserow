import { uuid } from '@baserow/modules/core/utils/string'

/**
 * For now this is a stub to allow everything to work like we already had the server
 * endpoints.
 */
export default (client) => {
  return {
    fetchAll(viewId) {
      // return client.get(`/database/views/${viewId}/decoration/`)
      return []
    },
    create(viewId, values) {
      // return client.post(`/database/views/${viewId}/decorations/`, values)
      return { data: { ...values, id: uuid() } }
    },
    get(viewDecorationId) {
      // return client.get(`/database/views/decoration/${viewDecorationId}/`)
      return {}
    },
    update(viewDecorationId, values) {
      /* return client.patch(
        `/database/views/decoration/${viewDecorationId}/`,
        values
      ) */
      return { data: { ...values } }
    },
    delete(viewDecorationId) {
      // return client.delete(`/database/views/decoration/${viewDecorationId}/`)
    },
  }
}

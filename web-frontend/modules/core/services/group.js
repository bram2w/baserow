import { client } from './client'

export default {
  fetchAll() {
    return client.get('/groups/')
  },
  create(values) {
    return client.post('/groups/', values)
  },
  update(id, values) {
    return client.patch(`/groups/${id}/`, values)
  },
  delete(id) {
    return client.delete(`/groups/${id}/`)
  },
}

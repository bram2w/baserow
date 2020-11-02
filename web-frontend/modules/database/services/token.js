export default (client) => {
  return {
    fetchAll() {
      return client.get('/database/tokens/')
    },
    create(values) {
      return client.post('/database/tokens/', values)
    },
    update(tokenId, values) {
      return client.patch(`/database/tokens/${tokenId}/`, values)
    },
    rotateKey(tokenId) {
      return client.patch(`/database/tokens/${tokenId}/`, {
        rotate_key: true,
      })
    },
    delete(tokenId, values) {
      return client.delete(`/database/tokens/${tokenId}/`)
    },
  }
}

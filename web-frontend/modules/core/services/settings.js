export default (client) => {
  return {
    get() {
      return client.get('/settings/')
    },
    update(values) {
      return client.patch('/settings/update/', values)
    },
  }
}

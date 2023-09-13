export default (client) => {
  return {
    update(builderId, values) {
      return client.patch(`builder/${builderId}/theme/`, values)
    },
  }
}

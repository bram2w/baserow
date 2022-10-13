export default (client) => {
  return {
    get(group) {
      return client.get(`/groups/${group.id}/permissions/`)
    },
  }
}

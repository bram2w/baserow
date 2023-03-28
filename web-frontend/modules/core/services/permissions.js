export default (client) => {
  return {
    get(workspace) {
      return client.get(`/workspaces/${workspace.id}/permissions/`)
    },
  }
}

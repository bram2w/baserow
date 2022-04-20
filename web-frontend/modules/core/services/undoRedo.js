export default (client) => {
  return {
    undo(scopes) {
      return client.patch(`/user/undo/`, {
        scopes,
      })
    },
    redo(scopes) {
      return client.patch(`/user/redo/`, {
        scopes,
      })
    },
  }
}

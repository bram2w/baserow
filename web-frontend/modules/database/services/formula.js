export default (client) => {
  return {
    type(formulaId, formula) {
      return client.post(`/database/formula/${formulaId}/type/`, { formula })
    },
  }
}

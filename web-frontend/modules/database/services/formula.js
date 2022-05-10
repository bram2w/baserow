export default (client) => {
  return {
    type(tableId, fieldName, formula) {
      return client.post(`/database/formula/${tableId}/type/`, {
        formula,
        name: fieldName,
      })
    },
  }
}

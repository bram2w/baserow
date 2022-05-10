// The different types of undo/redo scopes available for the database module.
export const DATABASE_ACTION_SCOPES = {
  table(tableId) {
    return {
      table: tableId,
    }
  },
  view(viewId) {
    return {
      view: viewId,
    }
  },
}

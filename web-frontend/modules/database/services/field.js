import { UNDO_REDO_ACTION_GROUP_HEADER } from '@baserow/modules/database/utils/action'

export default (client) => {
  return {
    fetchAll(tableId) {
      return client.get(`/database/fields/table/${tableId}/`)
    },
    create(tableId, values, undoRedoActionGroupId = null) {
      const config = {}
      if (undoRedoActionGroupId != null) {
        config.headers = {
          [UNDO_REDO_ACTION_GROUP_HEADER]: undoRedoActionGroupId,
        }
      }
      return client.post(`/database/fields/table/${tableId}/`, values, config)
    },
    get(fieldId) {
      return client.get(`/database/fields/${fieldId}/`)
    },
    getUniqueRowValues(fieldId, limit = 10, splitCommaSeparated = false) {
      const config = {
        params: {
          limit,
        },
      }

      if (splitCommaSeparated) {
        config.params.split_comma_separated = 'true'
      }

      return client.get(
        `/database/fields/${fieldId}/unique_row_values/`,
        config
      )
    },
    update(fieldId, values) {
      return client.patch(`/database/fields/${fieldId}/`, values)
    },
    delete(fieldId) {
      return client.delete(`/database/fields/${fieldId}/`)
    },
  }
}

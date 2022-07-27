import { UNDO_REDO_ACTION_GROUP_HEADER } from '@baserow/modules/database/utils/action'
import addPublicAuthTokenHeader from '@baserow/modules/database/utils/publicView'

export default (client) => {
  return {
    fetchAll(
      tableId,
      includeFilters = false,
      includeSortings = false,
      includeDecorations = false
    ) {
      const config = {
        params: {},
      }
      const include = []

      if (includeFilters) {
        include.push('filters')
      }

      if (includeSortings) {
        include.push('sortings')
      }

      if (includeDecorations) {
        include.push('decorations')
      }

      if (include.length > 0) {
        config.params.include = include.join(',')
      }

      return client.get(`/database/views/table/${tableId}/`, config)
    },
    create(tableId, values) {
      return client.post(`/database/views/table/${tableId}/`, values)
    },
    get(
      viewId,
      includeFilters = false,
      includeSortings = false,
      includeDecorations = false
    ) {
      const config = {
        params: {},
      }
      const include = []
      if (includeFilters) {
        include.push('filters')
      }

      if (includeSortings) {
        include.push('sortings')
      }

      if (includeDecorations) {
        include.push('decorations')
      }

      if (include.length > 0) {
        config.params.include = include.join(',')
      }
      return client.get(`/database/views/${viewId}/`, config)
    },
    update(viewId, values) {
      return client.patch(`/database/views/${viewId}/`, values)
    },
    duplicate(viewId) {
      return client.post(`/database/views/${viewId}/duplicate/`)
    },
    order(tableId, order) {
      return client.post(`/database/views/table/${tableId}/order/`, {
        view_ids: order,
      })
    },
    delete(viewId) {
      return client.delete(`/database/views/${viewId}/`)
    },
    fetchFieldOptions(viewId) {
      return client.get(`/database/views/${viewId}/field-options/`)
    },
    updateFieldOptions({ viewId, values, undoRedoActionGroupId = null }) {
      const config = {}
      if (undoRedoActionGroupId != null) {
        config.headers = {
          [UNDO_REDO_ACTION_GROUP_HEADER]: undoRedoActionGroupId,
        }
      }
      return client.patch(
        `/database/views/${viewId}/field-options/`,
        values,
        config
      )
    },
    rotateSlug(viewId) {
      return client.post(`/database/views/${viewId}/rotate-slug/`)
    },
    linkRowFieldLookup(slug, fieldId, page, search = null, size = 100) {
      const config = {
        params: {
          page,
          size,
        },
      }

      if (search !== null) {
        config.params.search = search
      }

      return client.get(
        `/database/views/${slug}/link-row-field-lookup/${fieldId}/`,
        config
      )
    },
    fetchPublicViewInfo(viewSlug, publicAuthToken = null) {
      const config = {}
      if (publicAuthToken) {
        addPublicAuthTokenHeader(config, publicAuthToken)
      }
      return client.get(`/database/views/${viewSlug}/public/info/`, config)
    },
  }
}

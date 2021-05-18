import { clone } from '@baserow/modules/core/utils/object'

/**
 * Registers the real time events related to the database module. When a message comes
 * in, the state of the stores will be updated to match the latest update. In some
 * cases some other events like refreshing all the data needs to be triggered.
 */
export const registerRealtimeEvents = (realtime) => {
  realtime.registerEvent('table_created', ({ store }, data) => {
    const database = store.getters['application/get'](data.table.database_id)
    if (database !== undefined) {
      store.dispatch('table/forceCreate', { database, data: data.table })
    }
  })

  realtime.registerEvent('table_updated', ({ store }, data) => {
    const database = store.getters['application/get'](data.table.database_id)
    if (database !== undefined) {
      const table = database.tables.find((table) => table.id === data.table.id)
      if (table !== undefined) {
        store.dispatch('table/forceUpdate', {
          database,
          table,
          values: data.table,
        })
      }
    }
  })

  realtime.registerEvent('tables_reordered', ({ store, app }, data) => {
    const database = store.getters['application/get'](data.database_id)
    if (database !== undefined) {
      store.commit('table/ORDER_TABLES', { database, order: data.order })
    }
  })

  realtime.registerEvent('table_deleted', ({ store }, data) => {
    const database = store.getters['application/get'](data.database_id)
    if (database !== undefined) {
      const table = database.tables.find((table) => table.id === data.table_id)
      if (table !== undefined) {
        store.dispatch('table/forceDelete', { database, table })
      }
    }
  })

  realtime.registerEvent('field_created', ({ store }, data) => {
    const table = store.getters['table/getSelected']
    if (table !== undefined && table.id === data.field.table_id) {
      store.dispatch('field/forceCreate', { table, values: data.field })
    }
  })

  realtime.registerEvent('field_updated', ({ store, app }, data) => {
    const field = store.getters['field/get'](data.field.id)
    if (field !== undefined) {
      const oldField = clone(field)
      // We want to wait for the table to reload before actually updating the field
      // in order to prevent incompatible values for the field.
      const callback = async () => {
        await store.dispatch('field/forceUpdate', {
          field,
          oldField,
          data: data.field,
        })
      }
      if (store.getters['table/getSelectedId'] === data.field.table_id) {
        app.$bus.$emit('table-refresh', {
          callback,
          tableId: store.getters['table/getSelectedId'],
        })
      } else {
        // If the current page is not the table we don't have to wait for the
        // refresh so we can update the field right away.
        callback()
      }
    }
  })

  realtime.registerEvent('field_deleted', ({ store, app }, data) => {
    const field = store.getters['field/get'](data.field_id)
    if (field !== undefined) {
      store.dispatch('field/forceDelete', field)
      if (store.getters['table/getSelectedId'] === data.table_id) {
        app.$bus.$emit('table-refresh', {
          tableId: store.getters['table/getSelectedId'],
        })
      }
    }
  })

  realtime.registerEvent('row_created', (context, data) => {
    const { app, store } = context
    for (const viewType of Object.values(app.$registry.getAll('view'))) {
      viewType.rowCreated(
        context,
        data.table_id,
        store.getters['field/getAll'],
        store.getters['field/getPrimary'],
        data.row,
        'page/'
      )
    }
  })

  realtime.registerEvent('row_updated', (context, data) => {
    const { app, store } = context
    for (const viewType of Object.values(app.$registry.getAll('view'))) {
      viewType.rowUpdated(
        context,
        data.table_id,
        store.getters['field/getAll'],
        store.getters['field/getPrimary'],
        data.row_before_update,
        data.row,
        'page/'
      )
    }
  })

  realtime.registerEvent('row_deleted', (context, data) => {
    const { app, store } = context
    for (const viewType of Object.values(app.$registry.getAll('view'))) {
      viewType.rowDeleted(
        context,
        data.table_id,
        store.getters['field/getAll'],
        store.getters['field/getPrimary'],
        data.row,
        'page/'
      )
    }
  })

  realtime.registerEvent('view_created', ({ store }, data) => {
    if (store.getters['table/getSelectedId'] === data.view.table_id) {
      store.dispatch('view/forceCreate', { data: data.view })
    }
  })

  realtime.registerEvent('view_updated', ({ store, app }, data) => {
    const view = store.getters['view/get'](data.view.id)
    if (view !== undefined) {
      const filterType = view.filter_type
      const filtersDisabled = view.filters_disabled
      store.dispatch('view/forceUpdate', { view, values: data.view })
      if (
        store.getters['view/getSelectedId'] === view.id &&
        (filterType !== data.view.filter_type ||
          filtersDisabled !== data.view.filters_disabled)
      ) {
        app.$bus.$emit('table-refresh', {
          tableId: store.getters['table/getSelectedId'],
        })
      }
    }
  })

  realtime.registerEvent('views_reordered', ({ store, app }, data) => {
    const table = store.getters['table/getSelected']
    if (table !== undefined && table.id === data.table_id) {
      store.commit('view/ORDER_ITEMS', data.order)
    }
  })

  realtime.registerEvent('view_deleted', ({ store }, data) => {
    const view = store.getters['view/get'](data.view_id)
    if (view !== undefined) {
      store.dispatch('view/forceDelete', view)
    }
  })

  realtime.registerEvent('view_filter_created', ({ store, app }, data) => {
    const view = store.getters['view/get'](data.view_filter.view)
    if (view !== undefined) {
      store.dispatch('view/forceCreateFilter', {
        view,
        values: data.view_filter,
      })
      if (store.getters['view/getSelectedId'] === view.id) {
        app.$bus.$emit('table-refresh', {
          tableId: store.getters['table/getSelectedId'],
        })
      }
    }
  })

  realtime.registerEvent('view_filter_updated', ({ store, app }, data) => {
    const view = store.getters['view/get'](data.view_filter.view)
    if (view !== undefined) {
      const filter = view.filters.find(
        (filter) => filter.id === data.view_filter.id
      )
      if (filter !== undefined) {
        store.dispatch('view/forceUpdateFilter', {
          filter,
          values: data.view_filter,
        })
        if (store.getters['view/getSelectedId'] === view.id) {
          app.$bus.$emit('table-refresh', {
            tableId: store.getters['table/getSelectedId'],
          })
        }
      }
    }
  })

  realtime.registerEvent('view_filter_deleted', ({ store, app }, data) => {
    const view = store.getters['view/get'](data.view_id)
    if (view !== undefined) {
      const filter = view.filters.find(
        (filter) => filter.id === data.view_filter_id
      )
      if (filter !== undefined) {
        store.dispatch('view/forceDeleteFilter', { view, filter })
        if (store.getters['view/getSelectedId'] === view.id) {
          app.$bus.$emit('table-refresh', {
            tableId: store.getters['table/getSelectedId'],
          })
        }
      }
    }
  })

  realtime.registerEvent('view_sort_created', ({ store, app }, data) => {
    const view = store.getters['view/get'](data.view_sort.view)
    if (view !== undefined) {
      store.dispatch('view/forceCreateSort', {
        view,
        values: data.view_sort,
      })
      if (store.getters['view/getSelectedId'] === view.id) {
        app.$bus.$emit('table-refresh', {
          tableId: store.getters['table/getSelectedId'],
        })
      }
    }
  })

  realtime.registerEvent('view_sort_updated', ({ store, app }, data) => {
    const view = store.getters['view/get'](data.view_sort.view)
    if (view !== undefined) {
      const sort = view.sortings.find((sort) => sort.id === data.view_sort_id)
      if (sort !== undefined) {
        store.dispatch('view/forceUpdateSort', {
          sort,
          values: data.view_sort,
        })
        if (store.getters['view/getSelectedId'] === view.id) {
          app.$bus.$emit('table-refresh', {
            tableId: store.getters['table/getSelectedId'],
          })
        }
      }
    }
  })

  realtime.registerEvent('view_sort_deleted', ({ store, app }, data) => {
    const view = store.getters['view/get'](data.view_id)
    if (view !== undefined) {
      const sort = view.sortings.find((sort) => sort.id === data.view_sort_id)
      if (sort !== undefined) {
        store.dispatch('view/forceDeleteSort', { view, sort })
        if (store.getters['view/getSelectedId'] === view.id) {
          app.$bus.$emit('table-refresh', {
            tableId: store.getters['table/getSelectedId'],
          })
        }
      }
    }
  })

  realtime.registerEvent(
    'grid_view_field_options_updated',
    ({ store }, data) => {
      const view = store.getters['view/get'](data.grid_view_id)
      if (view !== null && view.id === store.getters['view/getSelectedId']) {
        store.dispatch(
          'page/view/grid/forceUpdateAllFieldOptions',
          data.grid_view_field_options
        )
      }
    }
  )
}

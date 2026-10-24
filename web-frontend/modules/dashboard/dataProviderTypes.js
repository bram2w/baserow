import { DataProviderType } from '@baserow/modules/core/dataProviderTypes'
import { getValueAtPath } from '@baserow/modules/core/utils/object'

export class DashboardFilterDataProviderType extends DataProviderType {
  static getType() {
    return 'dashboard_filter'
  }

  isValid(path) {
    return (
      path.length >= 1 &&
      path.length <= 2 &&
      /^[1-9][0-9]*$/.test(path[0]) &&
      (path.length === 1 || path[1] === '*' || /^[0-9]+$/.test(path[1]))
    )
  }

  get name() {
    return this.app.$i18n.t('dashboardFilter.providerName')
  }

  getDataContent({ storePrefix = '' }) {
    const getters = this.app.$store.getters
    const prefix = `${storePrefix}dashboardApplication/`
    return Object.fromEntries(
      getters[prefix + 'getFilters'].map((filter) => {
        const values = getters[prefix + 'getAppliedFilterValues'](filter.id)
        return [
          filter.id,
          filter.mode === 'dropdown' && filter.multiple
            ? values
            : values[0] || '',
        ]
      })
    )
  }

  getDataChunk(context, path) {
    return getValueAtPath(this.getDataContent(context), path)
  }

  getDataSchema({ storePrefix = '' }) {
    const filters =
      this.app.$store.getters[`${storePrefix}dashboardApplication/getFilters`]
    return {
      type: 'object',
      properties: Object.fromEntries(
        filters.map((filter, index) => [
          filter.id,
          {
            title: filter.label,
            order: index,
            ...(filter.mode === 'dropdown' && filter.multiple
              ? { type: 'array', items: { type: 'string' } }
              : { type: 'string' }),
          },
        ])
      ),
    }
  }
}

export class DashboardTableDataProviderType extends DataProviderType {
  static getType() {
    return 'table'
  }

  isValid(path) {
    return (
      path.length >= 1 &&
      /^[1-9][0-9]*$/.test(path[0]) &&
      (path.length === 1 || path[1] === '*' || /^[0-9]+$/.test(path[1])) &&
      (path.length < 3 ||
        path[2] === 'id' ||
        /^field_[1-9][0-9]*$/.test(path[2]))
    )
  }

  get name() {
    return this.app.$i18n.t('dataProviderType.dataSource')
  }

  getDataContent() {
    // Table values are resolved by the backend when loading filter options.
    return {}
  }

  getDataChunk(context, path) {
    return getValueAtPath(this.getDataContent(context), path)
  }

  getDataSchema({ storePrefix = '' }) {
    const getters = this.app.$store.getters
    const prefix = `${storePrefix}dashboardApplication/`
    const sourceIds = new Set(
      getters[prefix + 'getWidgets'].map((widget) => widget.data_source_id)
    )
    const properties = {}
    for (const source of getters[prefix + 'getDataSources']) {
      if (
        sourceIds.has(source.id) &&
        source.table_schema &&
        !Object.hasOwn(properties, source.table_id)
      ) {
        properties[source.table_id] = {
          ...source.table_schema,
          order: Object.keys(properties).length,
        }
      }
    }
    return { type: 'object', properties }
  }
}

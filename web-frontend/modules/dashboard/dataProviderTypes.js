import { DataProviderType } from '@baserow/modules/core/dataProviderTypes'
import { getValueAtPath } from '@baserow/modules/core/utils/object'

export class DashboardFilterDataProviderType extends DataProviderType {
  static getType() {
    return 'dashboard_filter'
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

export class DashboardDataSourceDataProviderType extends DataProviderType {
  static getType() {
    return 'data_source'
  }

  get name() {
    return this.app.$i18n.t('dataProviderType.dataSource')
  }

  getDataContent({ storePrefix = '' }) {
    const getters = this.app.$store.getters
    const prefix = `${storePrefix}dashboardApplication/`
    return Object.fromEntries(
      getters[prefix + 'getDataSources'].map((source) => {
        const widget = getters[prefix + 'getWidgets'].find(
          (item) => item.data_source_id === source.id
        )
        const content = widget
          ? getters[prefix + 'getDataForWidget'](widget.id)
          : null
        const service = source.type
          ? this.app.$registry.get('service', source.type)
          : null
        return [source.id, service?.returnsList ? content?.results : content]
      })
    )
  }

  getDataChunk(context, [sourceId, ...rest]) {
    const source = this.app.$store.getters[
      `${context.storePrefix || ''}dashboardApplication/getDataSourceById`
    ](Number(sourceId))
    if (!source?.type) return null
    const service = this.app.$registry.get('service', source.type)
    const path = service.returnsList
      ? rest.length >= 2
        ? [rest[0], ...service.prepareValuePath(source, rest.slice(1))]
        : rest
      : service.prepareValuePath(source, rest)
    return getValueAtPath(this.getDataContent(context)[sourceId], path)
  }

  getDataSchema({ storePrefix = '', dataSource }) {
    const sources =
      this.app.$store.getters[
        `${storePrefix}dashboardApplication/getDataSources`
      ]
    return {
      type: 'object',
      properties: Object.fromEntries(
        sources
          .filter((source) => source.type && source.id !== dataSource?.id)
          .flatMap((source, index) => {
            const schema = this.app.$registry
              .get('service', source.type)
              .getDataSchema(source)
            return schema
              ? [[source.id, { ...schema, title: source.name, order: index }]]
              : []
          })
      ),
    }
  }
}

import { DataProviderType } from '@baserow/modules/core/dataProviderTypes'
import GenerateSchema from 'generate-schema'

import _ from 'lodash'

export class DataSourceDataProviderType extends DataProviderType {
  constructor(...args) {
    super(...args)
    this.debouncedFetches = {}
  }

  static getType() {
    return 'data_source'
  }

  get needBackendContext() {
    return true
  }

  get name() {
    return this.app.i18n.t('dataProviderType.dataSource')
  }

  async init(applicationContext) {
    const dataSources = this.app.store.getters['dataSource/getPageDataSources'](
      applicationContext.page
    )

    // Dispatch the data sources
    await this.app.store.dispatch(
      'dataSourceContent/fetchPageDataSourceContent',
      {
        page: applicationContext.page,
        data: DataProviderType.getAllBackendContext(
          this.app.$registry.getAll('builderDataProvider'),
          applicationContext
        ),
        dataSources,
      }
    )
  }

  getDataChunk(applicationContext, [dataSourceId, ...rest]) {
    const content = this.getDataSourceContent(applicationContext, dataSourceId)

    return content ? _.get(content, rest.join('.')) : null
  }

  getDataSourceContent(applicationContext, dataSourceId) {
    const page = applicationContext.page
    const dataSourceContents =
      this.app.store.getters['dataSourceContent/getDataSourceContents'](page)

    return dataSourceContents[dataSourceId]
  }

  getDataSourceSchema(applicationContext, dataSourceId) {
    return GenerateSchema.json(
      this.getDataSourceContent(applicationContext, dataSourceId)
    )
  }

  getDataContent(applicationContext) {
    const page = applicationContext.page
    const dataSources =
      this.app.store.getters['dataSource/getPageDataSources'](page)

    return Object.fromEntries(
      dataSources.map((dataSource) => {
        return [
          dataSource.id,
          this.getDataSourceContent(applicationContext, dataSource.id),
        ]
      })
    )
  }

  getDataSchema(applicationContext) {
    const page = applicationContext.page
    const dataSources =
      this.app.store.getters['dataSource/getPageDataSources'](page)

    const dataSourcesSchema = Object.fromEntries(
      dataSources.map((dataSource) => {
        const dsSchema = this.getDataSourceSchema(
          applicationContext,
          dataSource.id
        )
        delete dsSchema.$schema
        return [dataSource.id, dsSchema]
      })
    )

    return { type: 'object', properties: dataSourcesSchema }
  }

  pathPartToDisplay(applicationContext, part, position) {
    if (position === 1) {
      const page = applicationContext?.page
      return this.app.store.getters['dataSource/getPageDataSourceById'](
        page,
        parseInt(part)
      )?.name
    }

    return super.pathPartToDisplay(applicationContext, part, position)
  }
}

export class PageParameterDataProviderType extends DataProviderType {
  static getType() {
    return 'page_parameter'
  }

  get name() {
    return this.app.i18n.t('dataProviderType.pageParameter')
  }

  async init(applicationContext) {
    const { page, mode, pageParamsValue } = applicationContext
    if (mode === 'editing') {
      // Generate fake values for the parameters
      await Promise.all(
        page.path_params.map(({ name, type }) =>
          this.app.store.dispatch('pageParameter/setParameter', {
            page,
            name,
            value: type === 'numeric' ? 1 : 'test',
          })
        )
      )
    } else {
      // Read parameters from the application context
      await Promise.all(
        Object.entries(pageParamsValue).map(([name, value]) =>
          this.app.store.dispatch('pageParameter/setParameter', {
            page,
            name,
            value,
          })
        )
      )
    }
  }

  getDataChunk(applicationContext, path) {
    if (path.length !== 1) {
      return null
    }

    const [prop] = path
    const parameters = this.app.store.getters['pageParameter/getParameters'](
      applicationContext.page
    )

    if (parameters[prop] === undefined) {
      return null
    }

    return parameters[prop]
  }

  getBackendContext(applicationContext) {
    return this.getDataContent(applicationContext)
  }

  getDataContent(applicationContext) {
    return this.app.store.getters['pageParameter/getParameters'](
      applicationContext.page
    )
  }

  getDataSchema(applicationContext) {
    const page = applicationContext.page
    const toJSONType = { text: 'string', numeric: 'number' }

    return {
      type: 'object',
      properties: Object.fromEntries(
        (page?.path_params || []).map(({ name, type }) => [
          name,
          {
            name,
            type: toJSONType[type],
          },
        ])
      ),
    }
  }
}

import { DataProviderType } from '@baserow/modules/core/dataProviderTypes'

import { clone } from '@baserow/modules/core/utils/object'
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

  async init(runtimeFormulaContext) {
    const dataSources = this.app.store.getters['dataSource/getDataSources']

    await this.app.store.dispatch(
      'dataSourceContent/fetchPageDataSourceContent',
      {
        page: runtimeFormulaContext.applicationContext.page,
        data: runtimeFormulaContext.getAllBackendContext(),
        dataSources,
      }
    )
  }

  getDataChunk(runtimeFormulaContext, [dataSourceName, ...rest]) {
    // Get the data sources for the current page.
    const dataSources = this.app.store.getters['dataSource/getDataSources']

    const dataSource = dataSources.find(({ name }) => name === dataSourceName)

    if (!dataSource) {
      return null
    }

    // Update the dataSource content if needed
    this.app.store.dispatch('dataSourceContent/smartFetchDataSourceContent', {
      dataSource,
      data: runtimeFormulaContext.getAllBackendContext(),
    })

    const dataSourceContents =
      this.app.store.getters['dataSourceContent/getDataSourceContents']

    if (!dataSourceContents[dataSource.id]) {
      return null
    }

    // Returns the content from the store for reactivity
    return _.get(dataSourceContents[dataSource.id], rest.join('.'))
  }
}

export class PageParameterDataProviderType extends DataProviderType {
  static getType() {
    return 'page_parameter'
  }

  get name() {
    return this.app.i18n.t('dataProviderType.pageParameter')
  }

  async init(runtimeFormulaContext) {
    const { page, mode, pageParamsValue } =
      runtimeFormulaContext.applicationContext
    if (mode === 'editing') {
      // Generate fake values for the parameters
      await Promise.all(
        page.path_params.map(({ name, type }) =>
          this.app.store.dispatch('pageParameter/setParameter', {
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
            name,
            value,
          })
        )
      )
    }
  }

  getDataChunk(runtimeFormulaContext, path) {
    if (path.length !== 1) {
      return null
    }

    const [prop] = path
    const parameters = this.app.store.getters['pageParameter/getParameters']

    if (parameters[prop] === undefined) {
      return null
    }

    return parameters[prop]
  }

  getBackendContext() {
    return clone(this.app.store.getters['pageParameter/getParameters'])
  }
}

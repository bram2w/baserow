import { DataProviderType } from '@baserow/modules/core/dataProviderTypes'

import _ from 'lodash'
import { defaultValueForParameterType } from '@baserow/modules/builder/utils/params'

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
        data: DataProviderType.getAllDispatchContext(
          this.app.$registry.getAll('builderDataProvider'),
          applicationContext
        ),
        dataSources,
      }
    )
  }

  getDataChunk(applicationContext, [dataSourceId, ...rest]) {
    const dataSource = this.app.store.getters[
      'dataSource/getPageDataSourceById'
    ](applicationContext.page, parseInt(dataSourceId))

    const content = this.getDataSourceContent(applicationContext, dataSource)

    return content ? _.get(content, rest.join('.')) : null
  }

  getDataSourceContent(applicationContext, dataSource) {
    const dataSourceContents = this.app.store.getters[
      'dataSourceContent/getDataSourceContents'
    ](applicationContext.page)

    if (!dataSource?.type) {
      return null
    }

    const serviceType = this.app.$registry.get('service', dataSource.type)

    if (serviceType.returnsList) {
      return dataSourceContents[dataSource.id]?.results
    } else {
      return dataSourceContents[dataSource.id]
    }
  }

  getDataSourceSchema(dataSource) {
    if (dataSource?.type) {
      const serviceType = this.app.$registry.get('service', dataSource.type)
      return serviceType.getDataSchema(dataSource)
    }
    return null
  }

  getDataContent(applicationContext) {
    const page = applicationContext.page
    const dataSources =
      this.app.store.getters['dataSource/getPageDataSources'](page)

    return Object.fromEntries(
      dataSources.map((dataSource) => {
        return [
          dataSource.id,
          this.getDataSourceContent(applicationContext, dataSource),
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
        const dsSchema = this.getDataSourceSchema(dataSource)
        if (dsSchema) {
          delete dsSchema.$schema
        }
        return [dataSource.id, dsSchema]
      })
    )

    return { type: 'object', properties: dataSourcesSchema }
  }

  getPathTitle(applicationContext, pathParts) {
    if (pathParts.length === 2) {
      const page = applicationContext?.page
      const dataSourceId = parseInt(pathParts[1])
      return (
        this.app.store.getters['dataSource/getPageDataSourceById'](
          page,
          dataSourceId
        )?.name || `data_source_${dataSourceId}`
      )
    }
    return super.getPathTitle(applicationContext, pathParts)
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
            value: defaultValueForParameterType(type),
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
    const content = this.getDataContent(applicationContext)
    return _.get(content, path.join('.'))
  }

  getDispatchContext(applicationContext) {
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
            title: name,
            type: toJSONType[type],
          },
        ])
      ),
    }
  }
}

export class CurrentRecordDataProviderType extends DataProviderType {
  static getType() {
    return 'current_record'
  }

  get name() {
    return this.app.i18n.t('dataProviderType.currentRecord')
  }

  get indexKey() {
    // Prevent collision with user data
    return '__idx__'
  }

  get needBackendContext() {
    return true
  }

  // Loads all element contents
  async init(applicationContext) {
    const { page } = applicationContext

    await Promise.all(
      page.elements.map(async (element) => {
        if (element.data_source_id) {
          const dataSource = this.app.store.getters[
            'dataSource/getPageDataSourceById'
          ](page, element.data_source_id)

          const dispatchContext = DataProviderType.getAllDispatchContext(
            this.app.$registry.getAll('builderDataProvider'),
            { ...applicationContext, element }
          )

          try {
            // fetch the initial content
            return await this.app.store.dispatch(
              'elementContent/fetchElementContent',
              {
                element,
                dataSource,
                data: dispatchContext,
                range: [0, element.items_per_page],
              }
            )
          } catch (e) {
            // We don't want to block next dispatches so we do nothing, a notification
            // will be displayed by the component itself.
          }
        }
      })
    )
  }

  getDataChunk(applicationContext, path) {
    const content = this.getDataContent(applicationContext)
    return _.get(content, path.join('.'))
  }

  getDataContent(applicationContext) {
    const { element, recordIndex = 0 } = applicationContext

    if (!element) {
      return []
    }

    const rows =
      this.app.store.getters['elementContent/getElementContent'](element)

    const row = { [this.indexKey]: recordIndex, ...rows[recordIndex] }

    // Add the index value
    row[this.indexKey] = recordIndex

    return row
  }

  getDataSourceSchema(dataSource) {
    if (dataSource?.type) {
      const serviceType = this.app.$registry.get('service', dataSource.type)
      return serviceType.getDataSchema(dataSource)
    }
    return null
  }

  getDataSchema(applicationContext) {
    const { page, element: { data_source_id: dataSourceId } = {} } =
      applicationContext

    if (!dataSourceId) {
      return null
    }

    const dataSource = this.app.store.getters[
      'dataSource/getPageDataSourceById'
    ](page, dataSourceId)

    const schema = this.getDataSourceSchema(dataSource)
    const rowSchema = schema?.items?.properties || {}

    // Here we add the index property schema
    const properties = {
      [this.indexKey]: {
        type: 'number',
        title: this.app.i18n.t('currentRecordDataProviderType.index'),
      },
      ...rowSchema,
    }

    return { type: 'object', properties }
  }

  getPathTitle(applicationContext, pathParts) {
    if (pathParts.length === 1) {
      const { page, element: { data_source_id: dataSourceId } = {} } =
        applicationContext

      const dataSource = this.app.store.getters[
        'dataSource/getPageDataSourceById'
      ](page, dataSourceId)

      if (!dataSource) {
        return pathParts[0]
      }

      return this.app.i18n.t('currentRecordDataProviderType.firstPartName', {
        name: dataSource.name,
      })
    }

    return super.getPathTitle(applicationContext, pathParts)
  }
}

export class FormDataProviderType extends DataProviderType {
  static getType() {
    return 'form_data'
  }

  get name() {
    return this.app.i18n.t('dataProviderType.formData')
  }

  async init(applicationContext) {
    const { page } = applicationContext
    const elements = await this.app.store.getters['element/getElements'](page)
    const formElementTypes = Object.values(this.app.$registry.getAll('element'))
      .filter((elementType) => elementType.isFormElement)
      .map((elementType) => elementType.getType())
    const formElements = elements.filter((element) =>
      formElementTypes.includes(element.type)
    )

    return formElements.map((element) => {
      const elementType = this.app.$registry.get('element', element.type)
      const payload = {
        value: elementType.getInitialFormDataValue(element, applicationContext),
        type: elementType.formDataType,
      }
      return this.app.store.dispatch('formData/setFormData', {
        page,
        payload,
        elementId: element.id,
      })
    })
  }

  getDispatchContext(applicationContext) {
    return this.getDataContent(applicationContext)
  }

  getDataChunk(applicationContext, path) {
    const content = this.getDataContent(applicationContext)
    return _.get(content, path.join('')).value
  }

  getDataContent(applicationContext) {
    return this.app.store.getters['formData/getFormData'](
      applicationContext.page
    )
  }

  getDataSchema(applicationContext) {
    const { page } = applicationContext
    return {
      type: 'object',
      properties: Object.fromEntries(
        Object.entries(page.formData || {}).map(([elementId, { type }]) => {
          const element = this.app.store.getters['element/getElementById'](
            page,
            parseInt(elementId)
          )
          const elementType = this.app.$registry.get('element', element.type)
          const name = elementType.getDisplayName(element, applicationContext)
          const order = this.app.store.getters['element/getElementPosition'](
            page,
            element
          )
          return [
            elementId,
            {
              title: name,
              type,
              order,
            },
          ]
        })
      ),
    }
  }

  getPathTitle(applicationContext, pathParts) {
    if (pathParts.length === 2) {
      const elementId = parseInt(pathParts[1], 10)

      const element = this.app.store.getters['element/getElementById'](
        applicationContext.page,
        parseInt(elementId)
      )
      if (!element) {
        return this.app.i18n.t('formDataProviderType.nodeMissing')
      }
    }

    return super.getPathTitle(applicationContext, pathParts)
  }
}

export class UserDataProviderType extends DataProviderType {
  static getType() {
    return 'user'
  }

  get name() {
    return this.app.i18n.t('dataProviderType.user')
  }

  getDispatchContext(applicationContext) {
    const { isAuthenticated, id } = this.getDataContent(applicationContext)

    if (isAuthenticated) {
      return id
    } else {
      return null
    }
  }

  getDataChunk(applicationContext, path) {
    const content = this.getDataContent(applicationContext)
    return _.get(content, path.join('.'))
  }

  getDataContent(applicationContext) {
    return {
      isAuthenticated: this.app.store.getters['userSourceUser/isAuthenticated'],
      ...this.app.store.getters['userSourceUser/getUser'],
    }
  }

  getDataSchema(applicationContext) {
    return {
      type: 'object',
      properties: {
        is_authenticated: { title: 'isAuthenticated', type: 'boolean' },
        id: { type: 'number', title: 'id' },
        email: { type: 'string', title: 'email' },
        username: { type: 'string', title: 'username' },
      },
    }
  }
}

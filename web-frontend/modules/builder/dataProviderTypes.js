import _ from 'lodash'
import { DataProviderType } from '@baserow/modules/core/dataProviderTypes'
import { getValueAtPath } from '@baserow/modules/core/utils/object'

import { defaultValueForParameterType } from '@baserow/modules/builder/utils/params'
import { DEFAULT_USER_ROLE_PREFIX } from '@baserow/modules/builder/constants'
import { PAGE_PARAM_TYPE_VALIDATION_FUNCTIONS } from '@baserow/modules/builder/enums'

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
        data: DataProviderType.getAllDataSourceDispatchContext(
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
    return content ? getValueAtPath(content, rest.join('.')) : null
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
      dataSources
        .map((dataSource) => {
          const dsSchema = this.getDataSourceSchema(dataSource)
          if (dsSchema) {
            delete dsSchema.$schema
          }
          return [dataSource.id, dsSchema]
        })
        .filter(([, schema]) => schema)
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

export class DataSourceContextDataProviderType extends DataProviderType {
  static getType() {
    return 'data_source_context'
  }

  get name() {
    return this.app.i18n.t('dataProviderType.dataSourceContext')
  }

  getDataChunk({ page }, path) {
    const [dataSourceId, ...rest] = path

    const dataSource = this.app.store.getters[
      'dataSource/getPageDataSourceById'
    ](page, parseInt(dataSourceId))

    return getValueAtPath(dataSource.context_data, rest.join('.'))
  }

  getDataContent({ page }) {
    const dataSources =
      this.app.store.getters['dataSource/getPageDataSources'](page)

    return Object.fromEntries(
      dataSources.map((dataSource) => [dataSource.id, dataSource.context_data])
    )
  }

  getDataSchema({ page }) {
    const dataSources =
      this.app.store.getters['dataSource/getPageDataSources'](page)

    const contextDataSchema = Object.fromEntries(
      dataSources
        .filter((dataSource) => dataSource?.type)
        .map((dataSource) => [
          dataSource.id,
          this.app.$registry
            .get('service', dataSource.type)
            .getContextDataSchema(dataSource),
        ])
        .filter(([, schema]) => schema)
    )

    return { type: 'object', properties: contextDataSchema }
  }

  getPathTitle(applicationContext, pathParts) {
    if (pathParts.length === 2) {
      const page = applicationContext?.page
      const dataSourceId = parseInt(pathParts[1])
      return (
        this.app.store.getters['dataSource/getPageDataSourceById'](
          page,
          dataSourceId
        )?.name || `data_source_context_${dataSourceId}`
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
      // Read parameters value from the application context
      await Promise.all(
        page.path_params.map(({ name, type }) =>
          this.app.store.dispatch('pageParameter/setParameter', {
            page,
            name,
            value: PAGE_PARAM_TYPE_VALIDATION_FUNCTIONS[type](
              pageParamsValue[name]
            ),
          })
        )
      )
    }
  }

  getDataChunk(applicationContext, path) {
    const content = this.getDataContent(applicationContext)
    return getValueAtPath(content, path.join('.'))
  }

  getDataSourceDispatchContext(applicationContext) {
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

  getFirstCollectionAncestor(page, element) {
    if (!element) {
      return null
    }
    const elementType = this.app.$registry.get('element', element.type)
    if (elementType.isCollectionElement) {
      return element
    }
    const ancestors = this.app.store.getters['element/getAncestors'](
      page,
      element
    )
    for (const ancestor of ancestors) {
      const ancestorType = this.app.$registry.get('element', ancestor.type)
      if (ancestorType.isCollectionElement) {
        return ancestor
      }
    }
  }

  // Loads all element contents
  async init(applicationContext) {
    const { page } = applicationContext

    const elements = this.app.store.getters['element/getElementsOrdered'](page)

    await Promise.all(
      elements.map(async (element) => {
        if (element.data_source_id) {
          const dataSource = this.app.store.getters[
            'dataSource/getPageDataSourceById'
          ](page, element.data_source_id)

          const dispatchContext =
            DataProviderType.getAllDataSourceDispatchContext(
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

  getActionDispatchContext(applicationContext) {
    return applicationContext.recordIndex
  }

  getDataChunk(applicationContext, path) {
    const content = this.getDataContent(applicationContext)
    return getValueAtPath(content, path.join('.'))
  }

  getDataContent(applicationContext) {
    const { page, element, recordIndex = 0 } = applicationContext
    const collectionElement = this.getFirstCollectionAncestor(page, element)
    if (!collectionElement) {
      return []
    }

    const rows =
      this.app.store.getters['elementContent/getElementContent'](
        collectionElement
      )

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
    // `collectionField` is set by any collection element using collection fields
    // If we have a collection field in the application context, we are in
    // the context of a collection field inside a collection element.
    const { page, element, collectionField = null } = applicationContext
    const collectionElement = this.getFirstCollectionAncestor(page, element)
    const dataSourceId = collectionElement?.data_source_id

    if (
      // If the collection element doesn't have a data source configured
      !dataSourceId ||
      // Or if the collection element IS the current element and we are not in a
      // collection field
      (element.id === collectionElement.id && collectionField === null)
    ) {
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
      const { page, element } = applicationContext
      const collectionElement = this.getFirstCollectionAncestor(page, element)
      const dataSourceId = collectionElement?.data_source_id

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

  getActionDispatchContext(applicationContext) {
    return this.getDataContent(applicationContext)
  }

  /**
   * Responsible for filtering down an array of page elements to only those that
   * are form elements, and are in the same 'element namespace path' as one another.
   * For example:
   *
   * - HeadingRoot (path=[])
   *     * Can access `InputRoot`
   *     * Can access `InputContainer`
   * - InputRoot (path=[])
   * - FormContainer (path=[])
   *     - InputContainer (path=[])
   * - RepeatA (path=[])
   *     - InputOuter (path=[RepeatA.id])
   *     - HeadingOuter (path=[RepeatA.id])
   *         * Can access `InputOuter`
   *         * Can access `InputRoot`
   *         * Can access `InputContainer`
   *     - RepeatB (path=[RepeatA.id])
   *        - InputInner (path=[RepeatA.id, RepeatB.id])
   *        - HeadingInner (path=[RepeatA.id, RepeatB.id])
   *            * Can access `InputInner`
   *            * Can access `InputOuter`
   *            * Can access `InputRoot`
   *            * Can access `InputContainer`
   *
   * @param {Object} applicationContext - The application context object.
   * @param {Object} targetElement - The target element object.
   * @returns {Array} The filtered array of form elements in the same namespace as the target.
   */
  formElementsInNamespacePath(applicationContext, targetElement) {
    const { page } = applicationContext
    const targetNamespacePath =
      this.app.store.getters['element/getElementNamespacePath'](
        targetElement
      ).join('.')
    const elements = this.app.store.getters['element/getElementsOrdered'](page)
    return elements.filter((element) => {
      const elementType = this.app.$registry.get('element', element.type)
      if (!elementType.isFormElement) {
        // We only want to find accessible *form elements*.
        return false
      }
      const elementNamespacePath =
        this.app.store.getters['element/getElementNamespacePath'](element).join(
          '.'
        )
      return targetNamespacePath.startsWith(elementNamespacePath)
    })
  }

  getDataChunk(applicationContext, path) {
    const content = this.getDataContent(applicationContext)
    return getValueAtPath(content, path.join('.'))
  }

  getDataContent(applicationContext) {
    const formData = this.app.store.getters['formData/getFormData'](
      applicationContext.page
    )
    const { element: targetElement, recordIndexPath } = applicationContext
    const accessibleFormElements = this.formElementsInNamespacePath(
      applicationContext,
      targetElement
    )
    return Object.fromEntries(
      accessibleFormElements.map((element) => {
        const uniqueElementId = this.app.$registry
          .get('element', element.type)
          .uniqueElementId(element, recordIndexPath)
        const formEntry = getValueAtPath(formData, uniqueElementId)
        return [element.id, formEntry?.value]
      })
    )
  }

  getDataSchema(applicationContext) {
    const { page, element: targetElement } = applicationContext
    const accessibleFormElements = this.formElementsInNamespacePath(
      applicationContext,
      targetElement
    )
    return {
      type: 'object',
      properties: Object.fromEntries(
        accessibleFormElements.map((element) => {
          const elementType = this.app.$registry.get('element', element.type)
          const name = elementType.getDisplayName(element, applicationContext)
          const order = this.app.store.getters['element/getElementPosition'](
            page,
            element
          )
          return [
            element.id,
            {
              title: name,
              order,
              ...elementType.getDataSchema(element),
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

export class PreviousActionDataProviderType extends DataProviderType {
  static getType() {
    return 'previous_action'
  }

  get name() {
    return this.app.i18n.t('dataProviderType.previousAction')
  }

  get needBackendContext() {
    return true
  }

  getActionDispatchContext(applicationContext) {
    return this.getDataContent(applicationContext)
  }

  getDataChunk(applicationContext, path) {
    const content = this.getDataContent(applicationContext)
    return _.get(content, path.join('.'))
  }

  getWorkflowActionSchema(workflowAction) {
    if (workflowAction?.type) {
      const actionType = this.app.$registry.get(
        'workflowAction',
        workflowAction.type
      )
      return actionType.getDataSchema(workflowAction)
    }
    return null
  }

  getDataContent(applicationContext) {
    return applicationContext.previousActionResults
  }

  getDataSchema(applicationContext) {
    const page = applicationContext.page

    const previousActions = this.app.store.getters[
      'workflowAction/getElementPreviousWorkflowActions'
    ](page, applicationContext.element.id, applicationContext.workflowAction)

    const previousActionSchema = _.chain(previousActions)
      // Retrieve the associated schema for each action
      .map((workflowAction) => [
        workflowAction,
        this.getWorkflowActionSchema(workflowAction),
      ])
      // Remove actions without schema
      .filter(([_, schema]) => schema)
      // Add an index number to the schema title for each workflow action of
      // the same type.
      // For example if we have 2 update and create row actions we want their
      // titles to be: [Update row,  Create row, Update row 2, Create row 2]
      .groupBy('0.type')
      .flatMap((workflowActions) =>
        workflowActions.map(([workflowAction, schema], index) => [
          workflowAction.id,
          { ...schema, title: `${schema.title} ${index ? index + 1 : ''}` },
        ])
      )
      // Create the schema object
      .fromPairs()
      .value()
    return { type: 'object', properties: previousActionSchema }
  }

  getPathTitle(applicationContext, pathParts) {
    if (pathParts.length === 2) {
      const page = applicationContext?.page
      const workflowActionId = parseInt(pathParts[1])

      const action = this.app.store.getters[
        'workflowAction/getWorkflowActionById'
      ](page, workflowActionId)

      if (!action) {
        return `action_${workflowActionId}`
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

  getDataSourceDispatchContext(applicationContext) {
    const { is_authenticated: isAuthenticated, id } =
      this.getDataContent(applicationContext)

    if (isAuthenticated) {
      return id
    } else {
      return null
    }
  }

  getDataChunk(applicationContext, path) {
    const content = this.getDataContent(applicationContext)
    return getValueAtPath(content, path.join('.'))
  }

  getDataContent(applicationContext) {
    const loggedUser = this.app.store.getters['userSourceUser/getUser'](
      applicationContext.builder
    )

    const context = {
      is_authenticated: this.app.store.getters[
        'userSourceUser/isAuthenticated'
      ](applicationContext.builder),
      ...loggedUser,
    }

    if (context.role?.startsWith(DEFAULT_USER_ROLE_PREFIX)) {
      const userSourceName = this.app.store.getters[
        'userSource/getUserSourceByUId'
      ](applicationContext.builder, loggedUser.user_source_uid).name
      context.role = this.app.i18n.t('visibilityForm.rolesAllMembersOf', {
        name: userSourceName,
      })
    }

    return context
  }

  getDataSchema(applicationContext) {
    return {
      type: 'object',
      properties: {
        is_authenticated: {
          title: this.app.i18n.t('userDataProviderType.isAuthenticated'),
          type: 'boolean',
        },
        id: {
          type: 'number',
          title: this.app.i18n.t('userDataProviderType.id'),
        },
        email: {
          type: 'string',
          title: this.app.i18n.t('userDataProviderType.email'),
        },
        username: {
          type: 'string',
          title: this.app.i18n.t('userDataProviderType.username'),
        },
        role: {
          type: 'string',
          title: this.app.i18n.t('userDataProviderType.role'),
        },
      },
    }
  }
}

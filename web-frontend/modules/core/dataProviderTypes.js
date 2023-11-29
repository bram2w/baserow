import { Registerable } from '@baserow/modules/core/registry'

/**
 * A data provider gets data from the application context and populate the context for
 * the formula resolver.
 */
export class DataProviderType extends Registerable {
  DATA_TYPE_TO_ICON_MAP = {
    string: 'iconoir-text',
    number: 'baserow-icon-hashtag',
    boolean: 'baserow-icon-circle-checked',
  }

  UNKNOWN_DATA_TYPE_ICON = 'iconoir-question-mark'

  get name() {
    throw new Error('`name` must be set on the dataProviderType.')
  }

  /**
   * Should be true if the data provider needs backend context during its
   * initialisation phase.
   */
  get needBackendContext() {
    return false
  }

  /**
   * Initialize the data needed by the data provider if necessary. Used during the
   * page init phase to collect all the data for the first display.
   */
  async init(r) {}

  /**
   * Call init step of all given data providers according to the application context
   * @param {Array} dataProviders
   * @param {Object} applicationContext the application context.
   */
  static async initAll(dataProviders, applicationContext) {
    // First we initialize providers that doesn't need a backend context
    await Promise.all(
      Object.values(dataProviders)
        .filter((provider) => !provider.needBackendContext)
        .map((dataProvider) => dataProvider.init(applicationContext))
    )
    // Then we initialize those that need the backend context
    await Promise.all(
      Object.values(dataProviders)
        .filter((provider) => provider.needBackendContext)
        .map((dataProvider) => dataProvider.init(applicationContext))
    )
  }

  static getAllDispatchContext(dataProviders, applicationContext) {
    return Object.fromEntries(
      Object.values(dataProviders).map((dataProvider) => {
        return [
          dataProvider.type,
          dataProvider.getDispatchContext(applicationContext),
        ]
      })
    )
  }

  /**
   * Should return the context needed to be send to the backend for each dataProvider
   * to be able to solve the formulas on the backend.
   * @param {Object} applicationContext the application context.
   * @returns An object if the dataProvider wants to send something to the backend.
   */
  getDispatchContext(applicationContext) {
    return null
  }

  /**
   * Returns the actual data for the given path.
   * @param {object} applicationContext the application context.
   * @param {Array<str>} path the path of the data we want to get
   */
  getDataChunk(applicationContext, path) {
    throw new Error('.getDataChunk() must be set on the dataProviderType.')
  }

  /**
   * Return the data content for this data provider.
   * @param {Object} applicationContext the application context.
   * @returns {{$schema: string}}
   */
  getDataContent(applicationContext) {
    throw new Error('.getDataContent() must be set on the dataProviderType.')
  }

  /**
   * Return the schema of the data provided by this data provider
   * @param {Object} applicationContext the application context.
   * @returns {{type: string, properties: object}}
   */
  getDataSchema(applicationContext) {
    throw new Error('.getDataSchema() must be set on the dataProviderType.')
  }

  /**
   * This function returns an object that can be read by the data explorer to display
   * the data available from each data provider.
   *
   * Make sure to implement `getDataContent` and `getDataSchema` for every data provider
   * if they should show data in the data explorer.
   *
   * @param {Object} applicationContext the application context.
   * @returns {{identifier: string, name: string, nodes: []}}
   */
  getNodes(applicationContext) {
    const content = this.getDataContent(applicationContext)
    const schema = this.getDataSchema(applicationContext)

    if (schema === null) {
      return {}
    }

    const result = this._toNode(
      applicationContext,
      [this.type],
      content,
      schema
    )
    return result
  }

  /**
   * Recursive method to deeply compute the node tree for this data providers.
   * @param {Object} applicationContext the application context.
   * @param {Array<String>} pathParts the path to get to the current node.
   * @param {*} content the current node content.
   * @param {$schema: string} schema the current node schema.
   * @returns {{identifier: string, name: string, nodes: []}}
   */
  _toNode(applicationContext, pathParts, content, schema) {
    const identifier = pathParts.at(-1)
    const name = this.getPathTitle(applicationContext, pathParts)

    if (schema === null) {
      return {
        name,
        type: null,
        icon: this.UNKNOWN_DATA_TYPE_ICON,
        identifier,
      }
    }

    if (schema.type === 'array') {
      return {
        name,
        identifier,
        icon: this.getIconForType(schema.type),
        nodes: (content || []).map((item, index) =>
          this._toNode(
            applicationContext,
            [...pathParts, `${index}`],
            item,
            schema.items
          )
        ),
      }
    }

    if (schema.type === 'object') {
      return {
        name,
        identifier,
        icon: this.getIconForType(schema.type),
        nodes: Object.entries(schema.properties).map(
          ([identifier, subSchema]) =>
            this._toNode(
              applicationContext,
              [...pathParts, identifier],
              (content || {})[identifier],
              subSchema
            )
        ),
      }
    }

    return {
      name,
      type: schema.type,
      icon: this.getIconForType(schema.type),
      value: content,
      identifier,
    }
  }

  /**
   * This function gives you the icon that can be used by the data explorer given
   * the type of the data.
   * @param type - The type of the data
   * @returns {*|string} - The corresponding icon
   */
  getIconForType(type) {
    return this.DATA_TYPE_TO_ICON_MAP[type] || this.UNKNOWN_DATA_TYPE_ICON
  }

  /**
   * Returns the schema matching the given path
   * @param {Object} schemaNode
   * @param {Array<String>} pathParts
   * @returns the schema at the given path.
   */
  getSchemaNode(schemaNode, pathParts) {
    if (pathParts.length === 0) {
      return schemaNode
    }

    if (!schemaNode) {
      return null
    }

    const [first, ...rest] = pathParts

    if (schemaNode.type === 'array') {
      return this.getSchemaNode(schemaNode.items, rest)
    }

    if (schemaNode.type === 'object') {
      return this.getSchemaNode(schemaNode.properties[first], rest)
    }
  }

  /**
   * This function lets you hook into the path translation. Sometimes the path uses an
   * ID to reference an item, but we want to show the name of the item to the user
   * instead.
   * @param {Object} applicationContext the application context.
   * @param {Array<string>} pathParts - the path
   * @returns {Array<String>} - modified path part as it should be displayed to the user
   */
  getPathTitle(applicationContext, pathParts) {
    if (pathParts.length === 1) {
      return this.name
    }

    const [, ...rest] = pathParts

    const schema = this.getDataSchema(applicationContext)
    const schemaNode = this.getSchemaNode(schema, rest)

    return schemaNode?.title ? schemaNode.title : pathParts.at(-1)
  }

  getOrder() {
    return 0
  }
}

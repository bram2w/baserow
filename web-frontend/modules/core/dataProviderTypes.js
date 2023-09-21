import { Registerable } from '@baserow/modules/core/registry'

/**
 * A data provider gets data from the application context and populate the context for
 * the formula resolver.
 */
export class DataProviderType extends Registerable {
  DATA_TYPE_TO_ICON_MAP = {
    string: 'font',
    number: 'hashtag',
    boolean: 'check-square',
  }

  UNKNOWN_DATA_TYPE_ICON = 'question'

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

  static getAllBackendContext(dataProviders, applicationContext) {
    return Object.fromEntries(
      Object.values(dataProviders).map((dataProvider) => {
        return [
          dataProvider.type,
          dataProvider.getBackendContext(applicationContext),
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
  getBackendContext(applicationContext) {
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
   * @returns {{$schema: string}}
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

    return this._toNode(applicationContext, this.type, content, schema)
  }

  /**
   * Recursive method to deeply compute the node tree for this data providers.
   * @param {Object} applicationContext the application context.
   * @param {string} identifier the identifier for the current node.
   * @param {*} content the current node content.
   * @param {$schema: string} schema the current node schema.
   * @param {int} level the level of the current node in the data hierarchy.
   * @returns {{identifier: string, name: string, nodes: []}}
   */
  _toNode(applicationContext, identifier, content, schema, level = 0) {
    const name = this.pathPartToDisplay(applicationContext, identifier, level)
    if (schema.type === 'array') {
      return {
        name,
        identifier,
        icon: this.getIconForType(schema.type),
        nodes: content.map((item, index) =>
          this._toNode(
            applicationContext,
            `${index}`,
            item,
            schema.items,
            level + 1
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
              identifier,
              content[identifier],
              subSchema,
              level + 1
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
   * This function lets you hook into the path translation. Sometimes the path uses an
   * ID to reference an item, but we want to show the name of the item to the user
   * instead.
   * @param {Object} applicationContext the application context.
   * @param {String} part - raw path part as used by the formula
   * @param {String} position - index of the part in the path
   * @returns {Array<String>} - modified path part as it should be displayed to the user
   */
  pathPartToDisplay(applicationContext, part, position) {
    if (position === 0) {
      return this.name
    }
    return part
  }

  getOrder() {
    return 0
  }
}

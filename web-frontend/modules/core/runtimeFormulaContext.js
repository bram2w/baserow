import _ from 'lodash'

export class MissingDataProviderError extends Error {
  constructor(dataProviderName) {
    super()
    this.message = `The following data provider is missing: ${dataProviderName}`
    this.dataProviderName = dataProviderName
  }
}

export class UnresolvablePathError extends Error {
  constructor(dataProviderName, path) {
    super()
    this.message = `The path '${path}' can't be resolved in the data provider: ${dataProviderName}`
    this.dataProviderName = dataProviderName
    this.path = path
  }
}

export class RuntimeFormulaContext {
  constructor(dataProviders, applicationContext) {
    this.dataProviders = dataProviders
    this.applicationContext = applicationContext
  }

  async initAll() {
    // First we initialize providers that doesn't need a backend context
    await Promise.all(
      Object.values(this.dataProviders)
        .filter((provider) => !provider.needBackendContext)
        .map((dataProvider) => dataProvider.init(this))
    )
    // Then we initialize those that need the backend context
    await Promise.all(
      Object.values(this.dataProviders)
        .filter((provider) => provider.needBackendContext)
        .map((dataProvider) => dataProvider.init(this))
    )
  }

  getAllBackendContext() {
    return Object.fromEntries(
      Object.values(this.dataProviders).map((dataProvider) => {
        return [dataProvider.type, dataProvider.getBackendContext(this)]
      })
    )
  }

  /**
   * Returns the value for the given path. The first part of the path is
   * the data provider type, then the remaining parts are given to the data provider.
   *
   * @param {str} path the dotted path of the data we want to get.
   * @returns the data related to the path.
   */
  get(path) {
    const [providerName, ...rest] = _.toPath(path)

    const dataProviderType = this.dataProviders[providerName]
    if (!dataProviderType) {
      throw new MissingDataProviderError()
    }

    try {
      return dataProviderType.getDataChunk(this, rest)
    } catch (e) {
      throw new UnresolvablePathError(dataProviderType.type, rest.join('.'))
    }
  }
}

export default RuntimeFormulaContext

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
      return dataProviderType.getDataChunk(this.applicationContext, rest)
    } catch (e) {
      throw new UnresolvablePathError(dataProviderType.type, rest.join('.'))
    }
  }
}

export default RuntimeFormulaContext

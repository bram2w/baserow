const { unsupportedBaserowFieldTypes } = require('./constants')

/**
 * Fetches the fields of a table and converts them to an array with valid Zapier
 * field objects.
 */
const getRowInputValues = async (z, bundle) => {
  if (!bundle.inputData.tableID) {
    throw new Error('The `tableID` must be provided.')
  }

  const fieldsGetRequest = await z.request({
    url: `${bundle.authData.apiURL}/api/database/fields/table/${bundle.inputData.tableID}/`,
    method: 'GET',
    headers: {
      'Accept': 'application/json',
      'Authorization': `Token ${bundle.authData.apiToken}`,
    },
  })

  return fieldsGetRequest.json.map(v => {
    return mapBaserowFieldTypesToZapierTypes(v)
  })
}

/**
 * Fetches the fields and converts the input data to Baserow row compatible data.
 */
const prepareInputDataForBaserow = async (z, bundle) => {
  if (!bundle.inputData.tableID) {
    throw new Error('The `tableID` must be provided.')
  }

  const fieldsGetRequest = await z.request({
    url: `${bundle.authData.apiURL}/api/database/fields/table/${bundle.inputData.tableID}/`,
    method: 'GET',
    headers: {
      'Accept': 'application/json',
      'Authorization': `Token ${bundle.authData.apiToken}`,
    },
  })

  let rowData = { id: bundle.inputData.rowID }
  fieldsGetRequest
    .json
    .filter(
      (baserowField) =>
        baserowField.read_only
          || !unsupportedBaserowFieldTypes.includes(baserowField.type)
    )
    .filter((baserowField) => bundle.inputData.hasOwnProperty(baserowField.name))
    .forEach(baserowField => {
      let value = bundle.inputData[baserowField.name]

      if (baserowField.type === 'multiple_collaborators') {
        value = value.map(id => {
          return { id }}
        )
      }

      rowData[baserowField.name] = value
    })

  return rowData
}

/**
 * Converts the provided Baserow field type object to a Zapier compatible object.
 */
const mapBaserowFieldTypesToZapierTypes = (baserowField) => {
  const zapType = {
    key: baserowField.name,
    label: baserowField.name,
    type: 'string'
  }

  if (baserowField.type === 'long_text') {
    zapType.type = 'text'
  }

  if (baserowField.type === 'boolean') {
    zapType.type = 'boolean'
  }

  if (baserowField.type === 'number') {
    zapType.type = 'integer'

    if (baserowField.number_decimal_places > 0) {
      zapType.type = 'float'
    }
  }

  if (baserowField.type === 'boolean') {
    zapType.type = 'boolean'
  }

  if (baserowField.type === 'rating') {
    zapType.type = 'integer'
  }

  if (['single_select', 'multiple_select'].includes(baserowField.type)) {
    const choices = {}
    baserowField.select_options.forEach(el => {
      choices[`${el.id}`] = el.value
    })
    zapType.type = 'string'
    zapType.choices = choices
  }

  if (baserowField.type === 'multiple_select') {
    zapType.list = true
  }

  if (baserowField.type === 'link_row') {
    zapType.type = 'integer'
    zapType.helpText = 'Provide row ids that you want to link to.'
    zapType.list = true
  }

  if (baserowField.type === 'multiple_collaborators') {
    zapType.type = 'integer'
    zapType.helpText = 'Provide user ids that you want to link to.'
    zapType.list = true
  }

  if (baserowField.type === 'date' && !baserowField.date_include_time) {
    zapType.type = 'date'
    zapType.helpText =
      'the date fields accepts a date in ISO format (e.g. 2020-01-01)'
  }

  if (baserowField.type === 'date' && baserowField.date_include_time) {
    zapType.type = 'datetime'
    zapType.helpText =
      'the date fields accepts date and time in ISO format (e.g. 2020-01-01 12:00)'
  }

  if (
    baserowField.read_only
    || unsupportedBaserowFieldTypes.includes(baserowField.type)
  ) {
    // Read only and the file field are not supported.
    return
  }

  return zapType
}

module.exports = {
  getRowInputValues,
  prepareInputDataForBaserow,
  mapBaserowFieldTypesToZapierTypes,
}

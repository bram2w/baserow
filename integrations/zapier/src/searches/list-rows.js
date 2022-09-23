const { rowSample } = require('../samples/row')

const listRowsInputFields = [
  {
    key: 'tableID',
    label: 'Table ID',
    type: 'integer',
    required: true,
    helpText: 'Please enter the table ID where you want to get the rows from. You ' +
      'can find the ID by clicking on the three dots next to the table. It\'s the ' +
      'number between brackets.'
  },
  {
    key: 'page',
    label: 'page',
    helpText: 'Defines which page of rows should be returned.',
    type: 'string',
    default: '1'
  },
  {
    key: 'size',
    label: 'size',
    helpText: 'Defines how many rows should be returned per page.',
    type: 'string',
    default: '100'
  },
  {
    key: 'search',
    label: 'search',
    helpText:
      'If provided only rows with cell data that matches the search query ' +
      'are going to be returned.',
    type: 'string',
  },
]

const listRows = async (z, bundle) => {
  let params = {
    'size': bundle.inputData.size,
    'page': bundle.inputData.page,
    'user_field_names': 'true'
  }

  if (bundle.inputData.search) {
    params['search'] = bundle.inputData.search
  }

  const rowGetRequest = await z.request({
      url: `${bundle.authData.apiURL}/api/database/rows/table/${bundle.inputData.tableID}/`,
      method: 'GET',
      headers: {
          'Accept': 'application/json',
          'Authorization': `Token ${bundle.authData.apiToken}`,
      },
      params
  })

  // Modify array to be an single object, so it will display as 'row1-Name'.
  let data = {}
  rowGetRequest.json.results.forEach((row, index) => {
    for (const [key, value] of Object.entries(row)) {
      data[`row${index + 1}-${key}`] = value
    }
  })

  // The search actions needs to be array of object with only one object. Other
  // are not displayed in the UI.
  return [data]
}

module.exports = {
  key: 'listRows',
  noun: 'Row',
  display: {
    label: 'List Rows',
    description: 'Finds a page of rows in a given table.'
  },
  operation: {
    perform: listRows,
    sample: rowSample,
    inputFields: listRowsInputFields
  }
}

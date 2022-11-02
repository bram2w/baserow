const { rowSample } = require('../samples/row')

const getSingleRowInputFields = [
  {
    key: 'tableID',
    label: 'Table ID',
    type: 'integer',
    required: true,
    helpText: 'Please enter the table ID where you want to get the row from. You can ' +
      'find the ID by clicking on the three dots next to the table. It\'s the number ' +
      'between brackets.'
  },
  {
    key: 'rowID',
    label: 'Row ID',
    type: 'integer',
    required: true,
    helpText: 'Please enter the ID of the row that you want to get.'
  },
]

const getSingleRow = async (z, bundle) => {
  const rowGetRequest = await z.request({
    url: `${bundle.authData.apiURL}/api/database/rows/table/${bundle.inputData.tableID}/${bundle.inputData.rowID}/`,
    method: 'GET',
    headers: {
      'Accept': 'application/json',
      'Authorization': `Token ${bundle.authData.apiToken}`,
    },
    params: {
      'user_field_names': 'true',
    },
  })

  return [rowGetRequest.json]
}

module.exports = {
  key: 'getSingleRow',
  noun: 'Row',
  display: {
    label: 'Get Single Row',
    description: 'Finds a single row in a given table.'
  },
  operation: {
    perform: getSingleRow,
    sample: rowSample,
    inputFields: getSingleRowInputFields
  }
}

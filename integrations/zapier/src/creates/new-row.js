const { rowSample } = require('../samples/row')
const {
  getRowInputValues,
  prepareInputDataForBaserow
} = require('../helpers')

const rowInputFields = [
  {
    key: 'tableID',
    label: 'Table ID',
    type: 'integer',
    required: true,
    altersDynamicFields: true,
    helpText: 'Please enter the table ID where the row must be created in. You can ' +
      'find the ID by clicking on the three dots next to the table. It\'s the number ' +
      'between brackets.'
  },
]

const createRow = async (z, bundle) => {
  const rowData = await prepareInputDataForBaserow(z, bundle)
  const rowPostRequest = await z.request({
    url: `${bundle.authData.apiURL}/api/database/rows/table/${bundle.inputData.tableID}/`,
    method: 'POST',
    headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': `Token ${bundle.authData.apiToken}`,
    },
    params: {
      'user_field_names': 'true',
    },
    body: rowData,
  })

  return rowPostRequest.json
}

module.exports = {
  key: 'newRow',
  noun: 'Row',
  display: {
    label: 'Create Row',
    description: 'Creates a new row.'
  },
  operation: {
    perform: createRow,
    sample: rowSample,
    inputFields: [...rowInputFields, getRowInputValues]
  }
}

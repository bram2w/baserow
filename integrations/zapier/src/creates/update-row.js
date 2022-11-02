const { rowSample } = require('../samples/row')
const {
  getRowInputValues,
  prepareInputDataForBaserow
} = require('../helpers')

const updateRowInputFields = [
  {
    key: 'tableID',
    label: 'Table ID',
    type: 'integer',
    required: true,
    altersDynamicFields: true,
    helpText: 'Please enter the table ID where the row must be updated in. You can ' +
      'find the ID by clicking on the three dots next to the table. It\'s the ' +
      'number between brackets.'
  },
  {
    key: 'rowID',
    label: 'Row ID',
    type: 'integer',
    required: true,
    helpText: 'Please enter the row ID that must be updated.'
  },
]

const updateRow = async (z, bundle) => {
  const rowData = await prepareInputDataForBaserow(z, bundle)
  const rowPatchRequest = await z.request({
    url: `${bundle.authData.apiURL}/api/database/rows/table/${bundle.inputData.tableID}/${bundle.inputData.rowID}/`,
    method: 'PATCH',
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

  return rowPatchRequest.json
}

module.exports = {
  key: 'updateRow',
  noun: 'Row',
  display: {
    label: 'Update Row',
    description: 'Updates an existing row.'
  },
  operation: {
    perform: updateRow,
    sample: rowSample,
    inputFields: [...updateRowInputFields, getRowInputValues]
  }
}

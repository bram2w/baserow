const { rowSample } = require('../samples/row')

const deleteRowInputFields = [
  {
    key: 'tableID',
    label: 'Table ID',
    type: 'integer',
    required: true,
    helpText: 'Please enter the table ID where the row must be deleted in. You can ' +
      'find the ID by clicking on the three dots next to the table. It\'s the number ' +
      'between brackets.'
  },
  {
    key: 'rowID',
    label: 'Row ID',
    type: 'integer',
    required: true,
    helpText: 'Please the row ID that must be deleted.'
  },
]

const DeleteRow = async (z, bundle) => {
  const rowDeleteRequest = await z.request({
    url: `${bundle.authData.apiURL}/api/database/rows/table/${bundle.inputData.tableID}/${bundle.inputData.rowID}/`,
    method: 'DELETE',
    headers: {
        'Accept': 'application/json',
        'Authorization': `Token ${bundle.authData.apiToken}`,
    },
  })

  return rowDeleteRequest.status === 204
    ? { message: `Row ${bundle.inputData.rowID} deleted successfully.` }
    : { message: 'A problem occurred during DELETE operation. The row was not deleted.' }
}

module.exports = {
  key: 'deleteRow',
  noun: 'Row',
  display: {
    label: 'Delete Row',
    description: 'Deletes an existing row.'
  },
  operation: {
    perform: DeleteRow,
    sample: rowSample,
    inputFields: deleteRowInputFields
  }
}

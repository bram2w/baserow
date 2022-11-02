const { rowSample } = require('../samples/row')

const rowInputFields = [
  {
    key: 'tableID',
    label: 'Table ID',
    type: 'integer',
    required: true,
    helpText: 'Please enter your Baserow table ID. You can find the ID by clicking' +
      ' on the three dots next to the table. It\'s the number between brackets.'
  }
]

const getCreatedOrUpdatedRows = async (z, bundle) => {
  const nowDate = new Date()
  let fromDate = new Date()
  // This is the recommended way of doing it according to Zapier support.
  fromDate.setHours(fromDate.getHours() - 2)

  const rows = []
  const size = 200
  let page = 1
  let pages = null
  while (page <= pages || pages === null) {
    const request = await z.request({
      url: `${bundle.authData.apiURL}/api/database/rows/table/${bundle.inputData.tableID}/`,
      method: 'GET',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': `Token ${bundle.authData.apiToken}`,
      },
      params: {
        size: size,
        page: page,
        'user_field_names': 'true',
        'filter_type': 'AND',
        'filter__field_updated_on__date_before': nowDate.toISOString(),
        'filter__field_updated_on__date_after': fromDate.toISOString()
      },
    })

    if (pages === null) {
      // Calculate the amount of pages based on the total count of the backend.
      pages = Math.ceil(request.json.count / size)
    }

    // Add the rows to one big array.
    rows.push(...request.json.results)

    // Increase the page because we have already fetched it.
    page++
  }

  // Zapier figures out the duplicates.
  return rows
}

module.exports = {
  key: 'rowCreatedOrUpdated',
  noun: 'Row',
  display: {
    label: 'Row Created or Updated',
    description: 'Trigger when a new row is created or an existing one is updated.'
  },
  operation: {
    type: 'polling',
    perform: getCreatedOrUpdatedRows,
    canPaginate: false,
    sample: rowSample,
    inputFields: rowInputFields
  }
}

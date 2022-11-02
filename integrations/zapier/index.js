const authentication = require('./authentication.js')

const deleteRowCreate = require('./src/creates/delete-row.js')
const newRowCreate = require('./src/creates/new-row.js')
const updateRowCreate = require('./src/creates/update-row.js')

const getSingleRowSearch = require('./src/searches/get-single-row.js')
const listRowsSearch = require('./src/searches/list-rows.js')

const rowCreatedTrigger = require('./src/triggers/row-created.js')
const rowUpdatedTrigger = require('./src/triggers/row-updated.js')
const rowUpdatedOrCreatedTrigger =require('./src/triggers/row-updated-or-created.js')

module.exports = {
  version: require('./package.json').version,
  platformVersion: require('zapier-platform-core').version,
  authentication: authentication,
  triggers: {
    [rowCreatedTrigger.key]: rowCreatedTrigger,
    [rowUpdatedTrigger.key]: rowUpdatedTrigger,
    [rowUpdatedOrCreatedTrigger.key]: rowUpdatedOrCreatedTrigger
  },
  searches: {
    [getSingleRowSearch.key]: getSingleRowSearch,
    [listRowsSearch.key]: listRowsSearch
  },
  creates: {
    [newRowCreate.key]: newRowCreate,
    [deleteRowCreate.key]: deleteRowCreate,
    [updateRowCreate.key]: updateRowCreate,
  },
  resources: {},
}

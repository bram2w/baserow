import TableService from '@/modules/database/services/table'
import { DatabaseApplication } from '@/modules/database/application'

export function populateTable(table) {
  table._ = {
    disabled: false,
    selected: false
  }
  return table
}

export const state = () => ({
  selected: {}
})

export const mutations = {
  ADD_ITEM(state, { database, table }) {
    populateTable(table)
    database.tables.push(table)
  },
  UPDATE_ITEM(state, { table, values }) {
    Object.assign(table, table, values)
  },
  SET_SELECTED(state, { database, table }) {
    Object.values(database.tables).forEach(item => {
      item._.selected = false
    })
    table._.selected = true
    state.selected = table
  },
  DELETE_ITEM(state, { database, id }) {
    const index = database.tables.findIndex(item => item.id === id)
    database.tables.splice(index, 1)
  }
}

export const actions = {
  /**
   * Create a new table based on the provided values and add it to the tables
   * of the provided database.
   */
  create({ commit, dispatch }, { database, values }) {
    const type = DatabaseApplication.getType()

    // Check if the provided database (application) has the correct type.
    if (database.type !== type) {
      throw new Error(
        `The provided database application doesn't have the required type 
        "${type}".`
      )
    }

    return TableService.create(database.id, values).then(({ data }) => {
      commit('ADD_ITEM', { database, table: data })
    })
  },
  /**
   * Update an existing table of the provided database with the provided tables.
   */
  update({ commit, dispatch }, { database, table, values }) {
    return TableService.update(table.id, values).then(({ data }) => {
      // Create a dict with only the values we want to update.
      const update = Object.keys(values).reduce((result, key) => {
        result[key] = data[key]
        return result
      }, {})
      commit('UPDATE_ITEM', { database, table, values: update })
    })
  },
  /**
   * Deletes an existing application.
   */
  delete({ commit, dispatch }, { database, table }) {
    return TableService.delete(table.id)
      .then(() => {
        return dispatch('forceDelete', { database, table })
      })
      .catch(error => {
        if (error.response && error.response.status === 404) {
          return dispatch('forceDelete', { database, table })
        } else {
          throw error
        }
      })
  },
  /**
   *
   */
  forceDelete({ commit, dispatch }, { database, table }) {
    if (table._.selected) {
      // Redirect back to the dashboard because the table doesn't exist anymore.
      this.$router.push({ name: 'app' })
    }

    commit('DELETE_ITEM', { database, id: table.id })
  },
  /**
   * Select a table of a database.
   */
  select({ commit }, { database, table }) {
    commit('SET_SELECTED', { database, table })
    return { database, table }
  },
  /**
   * First it will preSelect the application to make sure the groups are
   * fetched, the correct group is selected, the related applications are
   * selected and the provided application id is selected. After that is will
   * check if the application has the correct type which is a database and makes
   * sure that the table actually belongs to that database. If so it will select
   * the table and return the database and table so it can be used.
   */
  preSelect({ dispatch, getters, rootGetters }, { databaseId, tableId }) {
    // Preselect the application
    return dispatch('application/preSelect', databaseId, { root: true }).then(
      database => {
        const type = DatabaseApplication.getType()

        // Check if the just selected application has the correct type because
        // it needs to have tables.
        if (database.type !== type) {
          throw new Error(
            `The application doesn't have the required ${type} type.`
          )
        }

        // Check if the provided table id is found is the just selected
        // database.
        const index = database.tables.findIndex(item => item.id === tableId)
        if (index === -1) {
          throw new Error('The table is not found in the selected application.')
        }
        const table = database.tables[index]

        // Select the table table and return the database and table instance
        // when done.
        return dispatch('select', { database, table })
      }
    )
  }
}

export const getters = {}

export default {
  namespaced: true,
  state,
  getters,
  actions,
  mutations
}

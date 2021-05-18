import axios from 'axios'

import { StoreItemLookupError } from '@baserow/modules/core/errors'
import TableService from '@baserow/modules/database/services/table'
import { DatabaseApplicationType } from '@baserow/modules/database/applicationTypes'

export function populateTable(table) {
  table._ = {
    disabled: false,
    selected: false,
  }
  return table
}

export const state = () => ({
  // Indicates whether the table is loading. This is used to show a loading
  // animation when switching between views.
  loading: false,
  selected: {},
})

export const mutations = {
  ADD_ITEM(state, { database, table }) {
    populateTable(table)
    database.tables.push(table)
  },
  UPDATE_ITEM(state, { table, values }) {
    Object.assign(table, table, values)
  },
  ORDER_TABLES(state, { database, order }) {
    database.tables.forEach((table) => {
      const index = order.findIndex((value) => value === table.id)
      table.order = index === -1 ? 0 : index + 1
    })
  },
  SET_SELECTED(state, { database, table }) {
    Object.values(database.tables).forEach((item) => {
      item._.selected = false
    })
    table._.selected = true
    state.selected = table
  },
  UNSELECT(state) {
    if (!Object.prototype.hasOwnProperty.call(state.selected, '_')) {
      return
    }
    state.selected._.selected = false
    state.selected = {}
  },
  DELETE_ITEM(state, { database, id }) {
    const index = database.tables.findIndex((item) => item.id === id)
    database.tables.splice(index, 1)
  },
  SET_LOADING(state, value) {
    state.loading = value
  },
}

export const actions = {
  setLoading({ commit }, value) {
    commit('SET_LOADING', value)
  },
  /**
   * Create a new table based on the provided values and add it to the tables
   * of the provided database.
   */
  async create(
    { commit, dispatch },
    { database, values, initialData = null, firstRowHeader = true }
  ) {
    const type = DatabaseApplicationType.getType()

    // Check if the provided database (application) has the correct type.
    if (database.type !== type) {
      throw new Error(
        `The provided database application doesn't have the required type
        "${type}".`
      )
    }

    const { data } = await TableService(this.$client).create(
      database.id,
      values,
      initialData,
      firstRowHeader
    )
    dispatch('forceCreate', { database, data })

    return data
  },
  /**
   * Forcefully create an item in the store without making a call to the server.
   */
  forceCreate({ commit }, { database, data }) {
    commit('ADD_ITEM', { database, table: data })
  },
  /**
   * Update an existing table of the provided database with the provided tables.
   */
  async update({ commit, dispatch }, { database, table, values }) {
    const { data } = await TableService(this.$client).update(table.id, values)
    // Create a dict with only the values we want to update.
    const update = Object.keys(values).reduce((result, key) => {
      result[key] = data[key]
      return result
    }, {})

    dispatch('forceUpdate', { database, table, values: update })
  },
  /**
   * Forcefully update an item in the store without making a call to the server.
   */
  forceUpdate({ commit }, { database, table, values }) {
    commit('UPDATE_ITEM', { database, table, values })
  },
  /**
   * Updates the order of all the tables in a database.
   */
  async order({ commit, getters }, { database, order, oldOrder }) {
    commit('ORDER_TABLES', { database, order })

    try {
      await TableService(this.$client).order(database.id, order)
    } catch (error) {
      commit('ORDER_TABLES', { database, order: oldOrder })
      throw error
    }
  },
  /**
   * Deletes an existing application.
   */
  async delete({ commit, dispatch }, { database, table }) {
    try {
      await TableService(this.$client).delete(table.id)
      return dispatch('forceDelete', { database, table })
    } catch (error) {
      if (error.response && error.response.status === 404) {
        return dispatch('forceDelete', { database, table })
      } else {
        throw error
      }
    }
  },
  /**
   * Delete the table from the store only. It will not send a request for deleting
   * to the server.
   */
  forceDelete(context, { database, table }) {
    const { commit, rootGetters } = context

    // Call the table deleted event on all fields.
    rootGetters['field/getAll'].forEach((field) => {
      const fieldType = this.$registry.get('field', field.type)
      fieldType.tableDeleted(context, field, table, database)
    })

    if (table._.selected) {
      // Redirect back to the dashboard because the table doesn't exist anymore.
      this.$router.push({ name: 'dashboard' })
    }

    commit('DELETE_ITEM', { database, id: table.id })
  },
  /**
   * When selecting the table we will have to fetch all the views and fields that
   * belong to the table we want to select. While the user is waiting he will see a
   * loading icon in the related database and after that the table is selected.
   */
  async select({ commit, dispatch, getters }, { database, table }) {
    // If the table is already selected we don't have to fetch the views and fields.
    if (getters.getSelectedId === table.id) {
      return { database, table }
    }

    await axios.all([
      dispatch('view/fetchAll', table, { root: true }),
      dispatch('field/fetchAll', table, { root: true }),
    ])
    await dispatch('application/clearChildrenSelected', null, { root: true })
    commit('SET_SELECTED', { database, table })
    return { database, table }
  },
  /**
   * Selects a table based on the provided database (application) and table id. The
   * application will also be selected if it has not already been selected. Because the
   * table object is stored inside the database (application) object we have to check if
   * it exists in there, if so it will be selected.
   */
  async selectById(
    { dispatch, getters, rootGetters },
    { databaseId, tableId }
  ) {
    const database = await dispatch('application/selectById', databaseId, {
      root: true,
    })
    const type = DatabaseApplicationType.getType()

    // Check if the just selected application is a database
    if (database.type !== type) {
      throw new StoreItemLookupError(
        `The application doesn't have the required ${type} type.`
      )
    }

    // Check if the provided table id is found in the just selected database.
    const index = database.tables.findIndex((item) => item.id === tableId)
    if (index === -1) {
      throw new StoreItemLookupError(
        'The table is not found in the selected application.'
      )
    }
    const table = database.tables[index]

    return dispatch('select', { database, table })
  },
  /**
   * Unselect the selected table.
   */
  unselect({ commit, dispatch, getters }) {
    commit('UNSELECT')
  },
}

export const getters = {
  getSelected: (state) => {
    return state.selected
  },
  getSelectedId(state) {
    return state.selected.id || 0
  },
}

export default {
  namespaced: true,
  state,
  getters,
  actions,
  mutations,
}

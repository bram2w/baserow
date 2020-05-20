import FieldService from '@baserow/modules/database/services/field'
import { clone } from '@baserow/modules/core/utils/object'

export function populateField(field, registry) {
  const type = registry.get('field', field.type)

  field._ = {
    type: type.serialize(),
    loading: false,
  }
  return type.populate(field)
}

export const state = () => ({
  types: {},
  loading: false,
  loaded: false,
  primary: null,
  items: [],
})

export const mutations = {
  SET_ITEMS(state, applications) {
    state.items = applications
  },
  SET_LOADING(state, value) {
    state.loading = value
  },
  SET_ITEM_LOADING(state, { field, value }) {
    if (!Object.prototype.hasOwnProperty.call(field, '_')) {
      return
    }
    field._.loading = value
  },
  SET_LOADED(state, value) {
    state.loaded = value
  },
  SET_PRIMARY(state, item) {
    state.primary = item
  },
  ADD_ITEM(state, item) {
    state.items.push(item)
  },
  UPDATE_ITEM(state, { id, values }) {
    const index = state.items.findIndex((item) => item.id === id)
    state.items.splice(index, 1, values)
  },
  DELETE_ITEM(state, id) {
    const index = state.items.findIndex((item) => item.id === id)
    state.items.splice(index, 1)
  },
  SET_SELECTED(state, field) {
    Object.values(state.items).forEach((item) => {
      item._.selected = false
    })
    field._.selected = true
    state.selected = field
  },
  UNSELECT(state) {
    Object.values(state.items).forEach((item) => {
      item._.selected = false
    })
    state.selected = {}
  },
}

export const actions = {
  /**
   * Changes the loading state of a specific field.
   */
  setItemLoading({ commit }, { field, value }) {
    commit('SET_ITEM_LOADING', { field, value })
  },
  /**
   * Fetches all the fields of a given table. The is mostly called when the user
   * selects a different table.
   */
  async fetchAll({ commit, getters, dispatch }, table) {
    commit('SET_LOADING', true)
    commit('SET_LOADED', false)
    commit('UNSELECT', {})

    try {
      const { data } = await FieldService(this.$client).fetchAll(table.id)
      data.forEach((part, index, d) => {
        populateField(data[index], this.$registry)
      })

      const primaryIndex = data.findIndex((item) => item.primary === true)
      const primary =
        primaryIndex !== -1 ? data.splice(primaryIndex, 1)[0] : null
      commit('SET_PRIMARY', primary)

      commit('SET_ITEMS', data)
      commit('SET_LOADING', false)
      commit('SET_LOADED', true)
    } catch (error) {
      commit('SET_ITEMS', [])
      commit('SET_LOADING', false)

      throw error
    }
  },
  /**
   * Creates a new field with the provided type for the given table.
   */
  async create(context, { type, table, values }) {
    const { commit } = context

    if (Object.prototype.hasOwnProperty.call(values, 'type')) {
      throw new Error(
        'The key "type" is a reserved, but is already set on the ' +
          'values when creating a new field.'
      )
    }

    if (!this.$registry.exists('field', type)) {
      throw new Error(`A field with type "${type}" doesn't exist.`)
    }

    const fieldType = this.$registry.get('field', type)

    const postData = clone(values)
    postData.type = type

    let { data } = await FieldService(this.$client).create(table.id, postData)
    data = populateField(data, this.$registry)
    commit('ADD_ITEM', data)

    // Call the field created event on all the registered views because they might
    // need to change things in loaded data. For example the grid field will add the
    // field to all of the rows that are in memory.
    Object.values(this.$registry.getAll('view')).forEach((viewType) => {
      viewType.fieldCreated(context, table, data, fieldType)
    })
  },
  /**
   * Updates the values of the provided field.
   */
  async update({ commit, dispatch, getters }, { field, type, values }) {
    if (Object.prototype.hasOwnProperty.call(values, 'type')) {
      throw new Error(
        'The key "type" is a reserved, but is already set on the values when ' +
          'creating a new field.'
      )
    }

    if (!this.$registry.exists('field', type)) {
      throw new Error(`A field with type "${type}" doesn't exist.`)
    }

    const postData = clone(values)
    postData.type = type

    let { data } = await FieldService(this.$client).update(field.id, postData)
    data = populateField(data, this.$registry)
    if (field.primary) {
      commit('SET_PRIMARY', data)
    } else {
      commit('UPDATE_ITEM', { id: field.id, values: data })
    }
  },
  /**
   * Deletes an existing field with the provided id.
   */
  async delete({ commit, dispatch }, field) {
    try {
      await FieldService(this.$client).delete(field.id)
      dispatch('forceDelete', field)
    } catch (error) {
      // If the field to delete wasn't found we can just delete it from the
      // state.
      if (error.response && error.response.status === 404) {
        dispatch('forceDelete', field)
      } else {
        throw error
      }
    }
  },
  /**
   * Forcibly remove the field from the items  without calling the server.
   */
  forceDelete({ commit, dispatch }, field) {
    commit('DELETE_ITEM', field.id)
  },
}

export const getters = {
  isLoaded(state) {
    return state.loaded
  },
  get: (state) => (id) => {
    return state.items.find((item) => item.id === id)
  },
}

export default {
  namespaced: true,
  state,
  getters,
  actions,
  mutations,
}

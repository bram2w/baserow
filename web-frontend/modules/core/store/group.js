import GroupService from '@baserow/modules/core/services/group'
import {
  setGroupCookie,
  unsetGroupCookie,
} from '@baserow/modules/core/utils/group'

function populateGroup(group) {
  group._ = { loading: false, selected: false }
  return group
}

export const state = () => ({
  loaded: false,
  loading: false,
  items: [],
  selected: {},
})

export const mutations = {
  SET_LOADED(state, loaded) {
    state.loaded = loaded
  },
  SET_LOADING(state, loading) {
    state.loading = loading
  },
  SET_ITEMS(state, items) {
    // Set some default values that we might need later.
    state.items = items.map((item) => {
      item = populateGroup(item)
      return item
    })
  },
  SET_ITEM_LOADING(state, { group, value }) {
    if (!Object.prototype.hasOwnProperty.call(group, '-')) {
      return
    }
    group._.loading = value
  },
  ADD_ITEM(state, item) {
    item = populateGroup(item)
    state.items.push(item)
  },
  UPDATE_ITEM(state, { id, values }) {
    const index = state.items.findIndex((item) => item.id === id)
    Object.assign(state.items[index], state.items[index], values)
  },
  DELETE_ITEM(state, id) {
    const index = state.items.findIndex((item) => item.id === id)
    state.items.splice(index, 1)
  },
  SET_SELECTED(state, group) {
    Object.values(state.items).forEach((item) => {
      item._.selected = false
    })
    group._.selected = true
    state.selected = group
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
   * If not already loading or loaded it will trigger the fetchAll action which
   * will load all the groups for the user.
   */
  loadAll({ state, dispatch }) {
    if (!state.loaded && !state.loading) {
      dispatch('fetchAll')
    }
  },
  /**
   * Clears all the selected groups. Can be used when logging off.
   */
  clearAll({ commit, dispatch }) {
    commit('SET_ITEMS', [])
    commit('UNSELECT')
    commit('SET_LOADED', false)
    return dispatch('application/clearAll', undefined, { root: true })
  },
  /**
   * Changes the loading state of a specific group.
   */
  setItemLoading({ commit }, { group, value }) {
    commit('SET_ITEM_LOADING', { group, value })
  },
  /**
   * Fetches all the groups of an authenticated user.
   */
  async fetchAll({ commit }) {
    commit('SET_LOADING', true)

    try {
      const { data } = await GroupService.fetchAll()
      commit('SET_LOADED', true)
      commit('SET_ITEMS', data)
    } catch {
      commit('SET_ITEMS', [])
    }

    commit('SET_LOADING', false)
  },
  /**
   * Creates a new group with the given values.
   */
  async create({ commit }, values) {
    const { data } = await GroupService.create(values)
    commit('ADD_ITEM', data)
  },
  /**
   * Updates the values of the group with the provided id.
   */
  async update({ commit, dispatch }, { group, values }) {
    const { data } = await GroupService.update(group.id, values)
    // Create a dict with only the values we want to update.
    const update = Object.keys(values).reduce((result, key) => {
      result[key] = data[key]
      return result
    }, {})
    commit('UPDATE_ITEM', { id: group.id, values: update })
  },
  /**
   * Deletes an existing group with the provided id.
   */
  async delete({ commit, dispatch }, group) {
    try {
      await GroupService.delete(group.id)
      await dispatch('forceDelete', group)
    } catch (error) {
      // If the group to delete wasn't found we can just delete it from the
      // state.
      if (error.response && error.response.status === 404) {
        await dispatch('forceDelete', group)
      } else {
        throw error
      }
    }
  },
  /**
   * Forcibly remove the group from the items  without calling the server.
   */
  forceDelete({ commit, dispatch, rootGetters }, group) {
    if (group._.selected) {
      dispatch('unselect', group)
    }

    commit('DELETE_ITEM', group.id)
  },
  /**
   * Select a group and fetch all the applications related to that group.
   */
  select({ commit, dispatch }, group) {
    commit('SET_SELECTED', group)
    setGroupCookie(group.id, this.app.$cookies)
  },
  /**
   * Select a group by a given group id.
   */
  selectById({ dispatch, getters }, id) {
    const group = getters.get(id)
    if (group === undefined) {
      throw new Error(`Group with id ${id} is not found.`)
    }
    return dispatch('select', group)
  },
  /**
   * Unselect a group if selected and clears all the fetched applications.
   */
  unselect({ commit, dispatch, getters }, group) {
    commit('UNSELECT', {})
    unsetGroupCookie(this.app.$cookies)
    return dispatch('application/clearAll', group, { root: true })
  },
}

export const getters = {
  isLoaded(state) {
    return state.loaded
  },
  isLoading(state) {
    return state.loading
  },
  get: (state) => (id) => {
    return state.items.find((item) => item.id === id)
  },
  hasSelected(state) {
    return Object.prototype.hasOwnProperty.call(state.selected, 'id')
  },
  selectedId(state) {
    if (!Object.prototype.hasOwnProperty.call(state.selected, 'id')) {
      throw new Error('There is no selected group.')
    }

    return state.selected.id
  },
}

export default {
  namespaced: true,
  state,
  getters,
  actions,
  mutations,
}

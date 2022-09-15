import { StoreItemLookupError } from '@baserow/modules/core/errors'
import GroupService from '@baserow/modules/core/services/group'
import {
  setGroupCookie,
  unsetGroupCookie,
} from '@baserow/modules/core/utils/group'
import { CORE_ACTION_SCOPES } from '@baserow/modules/core/utils/undoRedoConstants'

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
    if (!Object.prototype.hasOwnProperty.call(group, '_')) {
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
  ORDER_ITEMS(state, order) {
    state.items.forEach((group) => {
      const index = order.findIndex((value) => value === group.id)
      group.order = index === -1 ? 0 : index + 1
    })
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
  ADD_GROUP_USER(state, { groupId, values }) {
    const groupIndex = state.items.findIndex((item) => item.id === groupId)
    if (groupIndex !== -1) {
      state.items[groupIndex].users.push(values)
    }
  },
  UPDATE_GROUP_USER(state, { groupId, id, values }) {
    const groupIndex = state.items.findIndex((item) => item.id === groupId)
    if (groupIndex === -1) {
      return
    }
    const usersIndex = state.items[groupIndex].users.findIndex(
      (item) => item.id === id
    )
    if (usersIndex === -1) {
      return
    }
    Object.assign(
      state.items[groupIndex].users[usersIndex],
      state.items[groupIndex].users[usersIndex],
      values
    )
  },
  DELETE_GROUP_USER(state, { groupId, id }) {
    const groupIndex = state.items.findIndex((item) => item.id === groupId)
    if (groupIndex === -1) {
      return
    }
    state.items[groupIndex].users = state.items[groupIndex].users.filter(
      (item) => item.id !== id
    )
  },
}

export const actions = {
  /**
   * If not already loading or loaded it will trigger the fetchAll action which
   * will load all the groups for the user.
   */
  async loadAll({ state, dispatch }) {
    if (!state.loaded && !state.loading) {
      await dispatch('fetchAll')
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
      const { data } = await GroupService(this.$client).fetchAll()
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
  async create({ commit, dispatch }, values) {
    const { data } = await GroupService(this.$client).create(values)
    dispatch('forceCreate', data)
    return data
  },
  /**
   * Forcefully create an item in the store without making a call to the server.
   */
  forceCreate({ commit }, values) {
    commit('ADD_ITEM', values)
  },
  /**
   * Updates the values of the group with the provided id.
   */
  async update({ commit, dispatch }, { group, values }) {
    const { data } = await GroupService(this.$client).update(group.id, values)
    // Create a dict with only the values we want to update.
    const update = Object.keys(values).reduce((result, key) => {
      result[key] = data[key]
      return result
    }, {})
    dispatch('forceUpdate', { group, values: update })
  },
  /**
   * Forcefully update the item in the store without making a call to the server.
   */
  forceUpdate({ commit }, { group, values }) {
    commit('UPDATE_ITEM', { id: group.id, values })
  },
  /**
   * Forcefully reorders the items in the store without making a call to the server.
   */
  forceOrder({ commit }, order) {
    commit('ORDER_ITEMS', order)
  },
  /**
   * Updates the order of the groups for the current user.
   */
  async order({ commit, getters }, { order, oldOrder }) {
    commit('ORDER_ITEMS', order)

    try {
      await GroupService(this.$client).order(order)
    } catch (error) {
      commit('ORDER_ITEMS', oldOrder)
      throw error
    }
  },
  /**
   * Makes the current authenticated user leave the group.
   */
  async leave({ commit, dispatch }, group) {
    await GroupService(this.$client).leave(group.id)
    await dispatch('forceDelete', group)
  },
  /**
   * Deletes an existing group with the provided id.
   */
  async delete({ commit, dispatch }, group) {
    try {
      await GroupService(this.$client).delete(group.id)
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
   * Forcefully remove the group from the items  without calling the server. The
   * delete event is also called for all the applications that are in the
   * group. This is needed so that we can redirect the user to another page if for
   * example a Table is open that has been deleted because the group has been deleted.
   */
  forceDelete({ commit, dispatch, rootGetters }, group) {
    dispatch('job/deleteForGroup', group, { root: true })
    const applications = rootGetters['application/getAllOfGroup'](group)
    applications.forEach((application) => {
      return dispatch('application/forceDelete', application, { root: true })
    })

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
    setGroupCookie(group.id, this.app)
    dispatch(
      'undoRedo/updateCurrentScopeSet',
      CORE_ACTION_SCOPES.group(group.id),
      {
        root: true,
      }
    )
  },
  /**
   * Select a group by a given group id.
   */
  selectById({ dispatch, getters }, id) {
    const group = getters.get(id)
    if (group === undefined) {
      throw new StoreItemLookupError(`Group with id ${id} is not found.`)
    }
    return dispatch('select', group)
  },
  /**
   * Unselect a group if selected and clears all the fetched applications.
   */
  unselect({ commit, dispatch, getters }, group) {
    commit('UNSELECT', {})
    unsetGroupCookie(this.app)
    dispatch('undoRedo/updateCurrentScopeSet', CORE_ACTION_SCOPES.group(null), {
      root: true,
    })
    return dispatch('application/clearAll', group, { root: true })
  },
  /**
   * Forcefully adds a group user in the list of group's users.
   */
  forceAddGroupUser({ commit }, { groupId, values }) {
    commit('ADD_GROUP_USER', { groupId, values })
  },
  /**
   * Forcefully updates a group user in the list of group's users
   * and updates group's permissions attr if the group user is the
   * same as the current user.
   */
  forceUpdateGroupUser({ commit, rootGetters }, { groupId, id, values }) {
    commit('UPDATE_GROUP_USER', { groupId, id, values })
    const userId = rootGetters['auth/getUserId']
    if (values.user_id === userId) {
      commit('UPDATE_ITEM', {
        id: groupId,
        values: { permissions: values.permissions },
      })
    }
  },
  /**
   * Forcefully updates user's properties based on userId across all group users
   * of all groups. Can be used e.g. to change the user's name across all group
   * users that represent the same user in the system.
   */
  forceUpdateGroupUserAttributes({ commit, rootGetters }, { userId, values }) {
    const groups = rootGetters['group/getAll']
    for (const group of groups) {
      const usersIndex = group.users.findIndex(
        (item) => item.user_id === userId
      )
      if (usersIndex !== -1) {
        commit('UPDATE_GROUP_USER', {
          groupId: group.id,
          id: group.users[usersIndex].id,
          values,
        })
      }
    }
  },
  /**
   * Forcefully deletes a group user in the list of group's users. If the
   * group user is the current user, the whole group is removed.
   */
  forceDeleteGroupUser({ commit, rootGetters }, { groupId, id, values }) {
    const userId = rootGetters['auth/getUserId']
    if (values.user_id === userId) {
      commit('DELETE_ITEM', { id: groupId })
    } else {
      commit('DELETE_GROUP_USER', { groupId, id })
    }
  },
  /**
   * Forcefully deletes a user by deleting various user group instances
   * in all groups where the user is present.
   */
  forceDeleteUser({ commit, rootGetters }, { userId }) {
    const groups = rootGetters['group/getAll']
    for (const group of groups) {
      const usersIndex = group.users.findIndex(
        (item) => item.user_id === userId
      )
      if (usersIndex !== -1) {
        commit('DELETE_GROUP_USER', {
          groupId: group.id,
          id: group.users[usersIndex].id,
        })
      }
    }
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
  getAll(state) {
    return state.items
  },
  getAllSorted(state) {
    return state.items.map((g) => g).sort((a, b) => a.order - b.order)
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
  getAllUsers(state) {
    const users = {}
    for (const group of state.items) {
      for (const user of group.users) {
        users[user.user_id] = user
      }
    }
    return users
  },
  getAllUsersByEmail(state) {
    const users = {}
    for (const group of state.items) {
      for (const user of group.users) {
        users[user.email] = user
      }
    }
    return users
  },
  getAllUsersByName(state) {
    const users = {}
    for (const group of state.items) {
      for (const user of group.users) {
        users[user.name] = user
      }
    }
    return users
  },
  getUserById: (state, getters) => (userId) => {
    const users = getters.getAllUsers
    return users[userId]
  },
  getUserByEmail: (state, getters) => (email) => {
    const users = getters.getAllUsersByEmail
    return users[email]
  },
  getUserByName: (state, getters) => (name) => {
    const users = getters.getAllUsersByName
    return users[name]
  },
}

export default {
  namespaced: true,
  state,
  getters,
  actions,
  mutations,
}

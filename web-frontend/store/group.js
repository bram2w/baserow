import GroupService from '@/services/group'
import { notify404 } from '@/utils/error'
import { setGroupCookie, unsetGroupCookie } from '@/utils/group'

function populateGroup(group) {
  group._ = { loading: false, selected: false }
  return group
}

export const state = () => ({
  loaded: false,
  loading: false,
  items: [],
  selected: {}
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
    state.items = items.map(item => {
      item = populateGroup(item)
      return item
    })
  },
  SET_ITEM_LOADING(state, { group, value }) {
    if (!group.hasOwnProperty('_')) {
      return
    }
    group._.loading = value
  },
  ADD_ITEM(state, item) {
    item = populateGroup(item)
    state.items.push(item)
  },
  UPDATE_ITEM(state, values) {
    const index = state.items.findIndex(item => item.id === values.id)
    Object.assign(state.items[index], state.items[index], values)
  },
  DELETE_ITEM(state, id) {
    const index = state.items.findIndex(item => item.id === id)
    state.items.splice(index, 1)
  },
  SET_SELECTED(state, group) {
    Object.values(state.items).forEach(item => {
      item._.selected = false
    })
    group._.selected = true
    state.selected = group
  },
  UNSELECT(state) {
    Object.values(state.items).forEach(item => {
      item._.selected = false
    })
    state.selected = {}
  }
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
  clearAll({ commit }) {
    commit('SET_ITEMS', [])
    commit('SET_LOADED', false)
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
  fetchAll({ commit }) {
    commit('SET_LOADING', true)

    return GroupService.fetchAll()
      .then(({ data }) => {
        commit('SET_LOADED', true)
        commit('SET_ITEMS', data)
      })
      .catch(() => {
        commit('SET_ITEMS', [])
      })
      .then(() => {
        commit('SET_LOADING', false)
      })
  },
  /**
   * Creates a new group with the given values.
   */
  create({ commit }, values) {
    return GroupService.create(values).then(({ data }) => {
      commit('ADD_ITEM', data)
    })
  },
  /**
   * Updates the values of the group with the provided id.
   */
  update({ commit, dispatch }, { group, values }) {
    return GroupService.update(group.id, values)
      .then(({ data }) => {
        commit('UPDATE_ITEM', data)
      })
      .catch(error => {
        notify404(
          dispatch,
          error,
          'Unable to rename',
          "You're unable to rename the group. This could be because " +
            "you're not part of the group."
        )
      })
  },
  /**
   * Deletes an existing group with the provided id.
   */
  delete({ commit, dispatch }, group) {
    return GroupService.delete(group.id)
      .then(() => {
        if (group._.selected) {
          dispatch('unselect', group)
        }

        commit('DELETE_ITEM', group.id)
      })
      .catch(error => {
        notify404(
          dispatch,
          error,
          'Unable to delete',
          "You're unable to delete the group. This could be because " +
            "you're not part of the group."
        )
      })
  },
  /**
   * Select a group and fetch all the applications related to that group.
   */
  select({ commit, dispatch }, group) {
    commit('SET_SELECTED', group)
    setGroupCookie(group.id, this.app.$cookies)
    return dispatch('application/fetchAll', group, { root: true })
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
  }
}

export const getters = {
  isLoaded(state) {
    return state.loaded
  },
  isLoading(state) {
    return state.loading
  },
  get: state => id => {
    return state.items.find(item => item.id === id)
  },
  hasSelected(state) {
    return state.selected.hasOwnProperty('id')
  },
  selectedId(state) {
    if (!state.selected.hasOwnProperty('id')) {
      throw new Error('There is no selected group.')
    }

    return state.selected.id
  }
}

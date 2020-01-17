import { ViewType } from '@/modules/database/viewTypes'
import ViewService from '@/modules/database/services/view'
import { clone } from '@/utils/object'

export function populateView(view, getters) {
  const type = getters.getType(view.type)

  view._ = {
    type: type.serialize(),
    selected: false,
    loading: false
  }
  return type.populate(view)
}

export const state = () => ({
  types: {},
  loading: false,
  loaded: false,
  items: [],
  selected: {}
})

export const mutations = {
  REGISTER(state, view) {
    state.types[view.type] = view
  },
  SET_ITEMS(state, applications) {
    state.items = applications
  },
  SET_LOADING(state, value) {
    state.loading = value
  },
  SET_ITEM_LOADING(state, { view, value }) {
    if (!view.hasOwnProperty('_')) {
      return
    }
    view._.loading = value
  },
  SET_LOADED(state, value) {
    state.loaded = value
  },
  ADD_ITEM(state, item) {
    state.items.push(item)
  },
  UPDATE_ITEM(state, { id, values }) {
    const index = state.items.findIndex(item => item.id === id)
    Object.assign(state.items[index], state.items[index], values)
  },
  DELETE_ITEM(state, id) {
    const index = state.items.findIndex(item => item.id === id)
    state.items.splice(index, 1)
  },
  SET_SELECTED(state, view) {
    Object.values(state.items).forEach(item => {
      item._.selected = false
    })
    view._.selected = true
    state.selected = view
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
   * Register a new view type with the registry. This is used for creating a new
   * view type that users can create.
   */
  register({ commit, getters }, view) {
    if (!(view instanceof ViewType)) {
      throw Error('The view must be an instance of ViewType.')
    }

    commit('REGISTER', view)
  },
  /**
   * Changes the loading state of a specific view.
   */
  setItemLoading({ commit }, { view, value }) {
    commit('SET_ITEM_LOADING', { view, value })
  },
  /**
   * Fetches all the views of a given table. The is mostly called when the user
   * selects a different table.
   */
  fetchAll({ commit, getters, dispatch, state }, table) {
    commit('SET_LOADING', true)
    commit('SET_LOADED', false)
    commit('UNSELECT', {})

    return ViewService.fetchAll(table.id)
      .then(({ data }) => {
        data.forEach((part, index, d) => {
          populateView(data[index], getters)
        })
        commit('SET_ITEMS', data)
        commit('SET_LOADING', false)
        commit('SET_LOADED', true)

        // @TODO REMOVE THIS!
        if (state.items.length > 0) {
          dispatch('select', state.items[0])
        }
        // END REMOVE
      })
      .catch(error => {
        commit('SET_ITEMS', [])
        commit('SET_LOADING', false)

        throw error
      })
  },
  /**
   * Creates a new view with the provided type for the given table.
   */
  create({ commit, getters, rootGetters, dispatch }, { type, table, values }) {
    if (values.hasOwnProperty('type')) {
      throw new Error(
        'The key "type" is a reserved, but is already set on the ' +
          'values when creating a new view.'
      )
    }

    if (!getters.typeExists(type)) {
      throw new Error(`A view with type "${type}" doesn't exist.`)
    }

    const data = clone(values)
    data.type = type
    return ViewService.create(table.id, data).then(({ data }) => {
      populateView(data, getters)
      commit('ADD_ITEM', data)
    })
  },
  /**
   * Updates the values of the view with the provided id.
   */
  update({ commit, dispatch }, { view, values }) {
    return ViewService.update(view.id, values).then(({ data }) => {
      // Create a dict with only the values we want to update.
      const update = Object.keys(values).reduce((result, key) => {
        result[key] = data[key]
        return result
      }, {})
      commit('UPDATE_ITEM', { id: view.id, values: update })
    })
  },
  /**
   * Deletes an existing view with the provided id.
   */
  delete({ commit, dispatch }, view) {
    return ViewService.delete(view.id)
      .then(() => {
        dispatch('forceDelete', view)
      })
      .catch(error => {
        // If the view to delete wasn't found we can just delete it from the
        // state.
        if (error.response && error.response.status === 404) {
          dispatch('forceDelete', view)
        } else {
          throw error
        }
      })
  },
  /**
   * Forcibly remove the view from the items  without calling the server.
   */
  forceDelete({ commit, dispatch }, view) {
    if (view._.selected) {
      dispatch('unselect', view)
    }

    commit('DELETE_ITEM', view.id)
  },
  /**
   * Select a view and fetch all the applications related to that view.
   */
  select({ commit, dispatch }, view) {
    commit('SET_SELECTED', view)
    return { view }
  },
  /**
   * Select a view by a given view id.
   */
  selectById({ dispatch, getters }, id) {
    const view = getters.get(id)
    if (view === undefined) {
      return new Error(`View with id ${id} is not found.`)
    }
    return dispatch('select', view)
  },
  /**
   * Unselect a view if selected.
   */
  unselect({ commit, dispatch, getters }, view) {
    commit('UNSELECT', {})
  }
}

export const getters = {
  hasSelected(state) {
    return state.selected.hasOwnProperty('_')
  },
  isLoaded(state) {
    return state.loaded
  },
  get: state => id => {
    return state.items.find(item => item.id === id)
  },
  typeExists: state => type => {
    return state.types.hasOwnProperty(type)
  },
  getType: state => type => {
    if (!state.types.hasOwnProperty(type)) {
      throw new Error(`A view with type "${type}" doesn't exist.`)
    }
    return state.types[type]
  }
}

export default {
  namespaced: true,
  state,
  getters,
  actions,
  mutations
}

import { ApplicationType } from '@/core/applicationTypes'
import ApplicationService from '@/services/application'
import { clone } from '@/utils/object'

function populateApplication(application, getters) {
  const type = getters.getType(application.type)

  application._ = {
    type: type.serialize(),
    loading: false,
    selected: false
  }
  return type.populate(application)
}

export const state = () => ({
  types: {},
  loading: false,
  loaded: false,
  items: [],
  selected: {}
})

export const mutations = {
  REGISTER(state, application) {
    state.types[application.type] = application
  },
  SET_ITEMS(state, applications) {
    state.items = applications
  },
  SET_LOADING(state, value) {
    state.loading = value
  },
  SET_LOADED(state, value) {
    state.loaded = value
  },
  SET_ITEM_LOADING(state, { application, value }) {
    application._.loading = value
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
  SET_SELECTED(state, application) {
    Object.values(state.items).forEach(item => {
      item._.selected = false
    })
    application._.selected = true
    state.selected = application
  },
  UNSELECT(state) {
    Object.values(state.items).forEach(item => {
      item._.selected = false
    })
    state.selected = {}
  },
  CLEAR_CHILDREN_SELECTED(state, { type, application }) {
    type.clearChildrenSelected(application)
  }
}

export const actions = {
  /**
   * Register a new application within the registry. The is commonly used when
   * creating an extension.
   */
  register({ commit, getters }, application) {
    if (!(application instanceof ApplicationType)) {
      throw Error('The application must be an instance of ApplicationType.')
    }

    commit('REGISTER', application)
  },
  /**
   * Changes the loading state of a specific item.
   */
  setItemLoading({ commit }, { application, value }) {
    commit('SET_ITEM_LOADING', { application, value })
  },
  /**
   * Fetches all the application of the authenticated user.
   */
  fetchAll({ commit, getters }) {
    commit('SET_LOADING', true)

    return ApplicationService.fetchAll()
      .then(({ data }) => {
        data.forEach((part, index, d) => {
          populateApplication(data[index], getters)
        })
        commit('SET_ITEMS', data)
        commit('SET_LOADING', false)
        commit('SET_LOADED', true)
      })
      .catch(error => {
        commit('SET_ITEMS', [])
        commit('SET_LOADING', false)

        throw error
      })
  },
  /**
   * Clears all the currently selected applications, this could be called when
   * the group is deleted of when the user logs off.
   */
  clearAll({ commit }) {
    commit('SET_ITEMS', [])
    commit('UNSELECT')
    commit('SET_LOADED', false)
  },
  /**
   * If called all the applications that are in the state will clear their
   * children active state if they have one.
   */
  clearChildrenSelected({ commit, getters }) {
    Object.values(getters.getAll).forEach(application => {
      const type = getters.getType(application.type)
      commit('CLEAR_CHILDREN_SELECTED', { type, application })
    })
  },
  /**
   * Creates a new application with the given type and values for the currently
   * selected group.
   */
  create({ commit, getters, rootGetters, dispatch }, { type, values }) {
    if (values.hasOwnProperty('type')) {
      throw new Error(
        'The key "type" is a reserved, but is already set on the ' +
          'values when creating a new application.'
      )
    }

    if (!getters.typeExists(type)) {
      throw new Error(`An application type with type "${type}" doesn't exist.`)
    }

    const data = clone(values)
    data.type = type
    return ApplicationService.create(
      rootGetters['group/selectedId'],
      data
    ).then(({ data }) => {
      populateApplication(data, getters)
      commit('ADD_ITEM', data)
    })
  },
  /**
   * Updates the values of an existing application.
   */
  update({ commit, dispatch, getters }, { application, values }) {
    return ApplicationService.update(application.id, values).then(
      ({ data }) => {
        // Create a dict with only the values we want to update.
        const update = Object.keys(values).reduce((result, key) => {
          result[key] = data[key]
          return result
        }, {})
        commit('UPDATE_ITEM', { id: application.id, values: update })
      }
    )
  },
  /**
   * Deletes an existing application.
   */
  delete({ commit, dispatch, getters }, application) {
    return ApplicationService.delete(application.id)
      .then(() => {
        const type = getters.getType(application.type)
        type.delete(application, this)
        commit('DELETE_ITEM', application.id)
      })
      .catch(error => {
        if (error.response && error.response.status === 404) {
          commit('DELETE_ITEM', application.id)
        } else {
          throw error
        }
      })
  },
  /**
   * Select an application.
   */
  select({ commit }, application) {
    commit('SET_SELECTED', application)
    return application
  },
  /**
   * Select an application by a given application id.
   */
  selectById({ dispatch, getters }, id) {
    const application = getters.get(id)
    if (application === undefined) {
      throw new Error(`Application with id ${id} is not found.`)
    }
    return dispatch('select', application)
  },
  /**
   * Unselect the
   */
  unselect({ commit }) {
    commit('UNSELECT', {})
  }
}

export const getters = {
  isLoading(state) {
    return state.loading
  },
  isLoaded(state) {
    return state.loaded
  },
  get: state => id => {
    return state.items.find(item => item.id === id)
  },
  getAll(state) {
    return state.items
  },
  typeExists: state => type => {
    return state.types.hasOwnProperty(type)
  },
  getType: state => type => {
    if (!state.types.hasOwnProperty(type)) {
      throw new Error(`An application type with type "${type}" doesn't exist.`)
    }
    return state.types[type]
  }
}

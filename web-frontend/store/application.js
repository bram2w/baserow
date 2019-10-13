import { Application } from '@/core/applications'
import ApplicationService from '@/services/application'
import { notify404, notifyError } from '@/utils/error'

function populateApplication(application, getters) {
  const type = getters.getApplicationByType(application.type)

  application._ = {
    type: type.serialize(),
    loading: false,
    selected: false
  }
  return application
}

export const state = () => ({
  applications: {},
  loading: false,
  items: [],
  selected: {}
})

export const mutations = {
  REGISTER(state, application) {
    state.applications[application.type] = application
  },
  SET_ITEMS(state, applications) {
    state.items = applications
  },
  SET_LOADING(state, value) {
    state.loading = value
  },
  SET_ITEM_LOADING(state, { application, value }) {
    application._.loading = value
  },
  ADD_ITEM(state, item) {
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
   * Register a new application within the registry. The is commonly used when
   * creating an extension.
   */
  register({ commit }, application) {
    if (!(application instanceof Application)) {
      throw Error('The application must be an instance of Application.')
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
   * Fetches all the applications of a given group. The is mostly called when
   * the user selects a different group.
   */
  fetchAll({ commit, getters, dispatch }, group) {
    commit('SET_LOADING', true)

    return ApplicationService.fetchAll(group.id)
      .then(({ data }) => {
        data.forEach((part, index, d) => {
          populateApplication(data[index], getters)
        })
        commit('SET_ITEMS', data)
      })
      .catch(error => {
        commit('SET_ITEMS', [])

        notify404(
          dispatch,
          error,
          'Unable to fetch applications',
          "You're unable to fetch the application of this group. " +
            "This could be because you're not part of the group."
        )
      })
      .then(() => {
        commit('SET_LOADING', false)
      })
  },
  /**
   * Clears all the currently selected applications, this could be called when
   * the group is deleted of when the user logs off.
   */
  clearAll({ commit }) {
    commit('SET_ITEMS', [])
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

    if (!getters.applicationTypeExists(type)) {
      throw new Error(`An application with type "${type}" doesn't exist.`)
    }

    values.type = type
    return ApplicationService.create(rootGetters['group/selectedId'], values)
      .then(({ data }) => {
        populateApplication(data, getters)
        commit('ADD_ITEM', data)
      })
      .catch(error => {
        notify404(
          dispatch,
          error,
          'Could not create application',
          "You're unable to create a new application for the selected " +
            "group. This could be because you're not part of the group."
        )
      })
  },
  /**
   * Updates the values of an existing application.
   */
  update({ commit, dispatch }, { application, values }) {
    return ApplicationService.update(application.id, values)
      .then(({ data }) => {
        commit('UPDATE_ITEM', data)
      })
      .catch(error => {
        notifyError(
          dispatch,
          error,
          'ERROR_USER_NOT_IN_GROUP',
          'Rename not allowed',
          "You're not allowed to rename the application because you're " +
            'not part of the group where the application is in.'
        )
      })
  },
  /**
   * Deletes an existing application.
   */
  delete({ commit, dispatch }, application) {
    return ApplicationService.delete(application.id)
      .then(() => {
        commit('DELETE_ITEM', application.id)
      })
      .catch(error => {
        notifyError(
          dispatch,
          error,
          'ERROR_USER_NOT_IN_GROUP',
          'Delete not allowed',
          "You're not allowed to rename the application because you're" +
            ' not part of the group where the application is in.'
        )
      })
  },
  /**
   * Select an application.
   */
  select({ commit }, application) {
    commit('SET_SELECTED', application)
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
  },
  /**
   * The preSelect action will eventually select an application, but it will
   * first check which information still needs to be loaded. For example if
   * no group or not the group where the application is in loaded it will then
   * first fetch that group and related application so that the sidebar is up
   * to date. In short it will make sure that the depending state of the given
   * application will be there.
   */
  preSelect({ dispatch, getters, rootGetters }, id) {
    // First we will check if the application is already in the items.
    const application = getters.get(id)

    // If the application is already selected we don't have to do anything.
    if (application !== undefined && application._.selected) {
      return
    }

    // This function will select a group by its id which will then automatically
    // fetch the applications related to that group. When done it will select
    // the provided application id.
    const selectGroupAndApplication = (groupId, applicationId) => {
      return dispatch('group/selectById', groupId, {
        root: true
      }).then(() => {
        return dispatch('selectById', applicationId)
      })
    }

    if (application !== undefined) {
      // If the application is already in the selected groups, which means that
      // the groups and applications are already loaded, we can just select that
      // application.
      dispatch('select', application)
    } else {
      // The application is not in the selected group so we need to figure out
      // in which he is by fetching the application.
      return ApplicationService.get(id).then(data => {
        if (!rootGetters['group/isLoaded']) {
          // If the groups are not already loaded we need to load them first.
          return dispatch('group/fetchAll', {}, { root: true }).then(() => {
            return selectGroupAndApplication(data.data.group.id, id)
          })
        } else {
          // The groups are already loaded so we
          return selectGroupAndApplication(data.data.group.id, id)
        }
      })
    }
  }
}

export const getters = {
  isLoading(state) {
    return state.loading
  },
  get: state => id => {
    return state.items.find(item => item.id === id)
  },
  applicationTypeExists: state => type => {
    return state.applications.hasOwnProperty(type)
  },
  getApplicationByType: state => type => {
    if (!state.applications.hasOwnProperty(type)) {
      throw new Error(`An application with type "${type}" doesn't exist.`)
    }
    return state.applications[type]
  }
}

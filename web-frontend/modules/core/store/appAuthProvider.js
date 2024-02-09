import AppAuthProviderService from '@baserow/modules/core/services/appAuthProvider'

const state = {}

const updateContext = {
  updateTimeout: null,
  promiseResolve: null,
  lastUpdatedValues: null,
}

const mutations = {
  ADD_ITEM(state, { userSource, appAuthProvider, beforeId = null }) {
    if (beforeId === null) {
      userSource.appAuthProviders.push(appAuthProvider)
    } else {
      const insertionIndex = userSource.appAuthProviders.findIndex(
        (e) => e.id === beforeId
      )
      userSource.appAuthProviders.splice(insertionIndex, 0, appAuthProvider)
    }
  },
  UPDATE_ITEM(
    state,
    { userSource, appAuthProvider: appAuthProviderToUpdate, values }
  ) {
    userSource.appAuthProviders.forEach((appAuthProvider) => {
      if (appAuthProvider.id === appAuthProviderToUpdate.id) {
        Object.assign(appAuthProvider, values)
      }
    })
  },
  DELETE_ITEM(state, { userSource, appAuthProviderId }) {
    const index = userSource.appAuthProviders.findIndex(
      (appAuthProvider) => appAuthProvider.id === appAuthProviderId
    )
    if (index > -1) {
      userSource.appAuthProviders.splice(index, 1)
    }
  },
  CLEAR_ITEMS(state, { userSource }) {
    userSource.appAuthProviders = []
  },
}

const actions = {
  forceCreate({ commit }, { userSource, appAuthProvider, beforeId = null }) {
    commit('ADD_ITEM', { userSource, appAuthProvider, beforeId })
  },
  forceUpdate({ commit }, { userSource, appAuthProvider, values }) {
    commit('UPDATE_ITEM', { userSource, appAuthProvider, values })
  },
  forceDelete({ commit, getters }, { userSource, appAuthProviderId }) {
    commit('DELETE_ITEM', { userSource, appAuthProviderId })
  },
  async create({ dispatch }, { userSource, appAuthProviderType, values }) {
    const { data: appAuthProvider } = await AppAuthProviderService(
      this.$client
    ).create(userSource.id, appAuthProviderType, values)

    await dispatch('forceCreate', { userSource, appAuthProvider })

    return appAuthProvider
  },
  async update(
    { dispatch, getters },
    { userSource, appAuthProviderId, values }
  ) {
    const appAuthProvidersOfUserSource = getters.getUserSources(userSource)
    const appAuthProvider = appAuthProvidersOfUserSource.find(
      ({ id }) => id === appAuthProviderId
    )
    const oldValues = {}
    const newValues = {}
    Object.keys(values).forEach((name) => {
      if (Object.prototype.hasOwnProperty.call(appAuthProvider, name)) {
        oldValues[name] = appAuthProvider[name]
        newValues[name] = values[name]
      }
    })

    await dispatch('forceUpdate', {
      userSource,
      appAuthProvider,
      values: newValues,
    })

    try {
      await AppAuthProviderService(this.$client).update(
        appAuthProvider.id,
        values
      )
    } catch (error) {
      await dispatch('forceUpdate', {
        userSource,
        appAuthProvider,
        values: oldValues,
      })
      throw error
    }
  },

  async debouncedUpdate(
    { dispatch, getters },
    { userSource, appAuthProviderId, values }
  ) {
    const appAuthProvider = getters.getAppAuthProviders.find(
      ({ id }) => id === appAuthProviderId
    )
    const oldValues = {}
    const newValues = {}
    Object.keys(values).forEach((name) => {
      if (Object.prototype.hasOwnProperty.call(appAuthProvider, name)) {
        oldValues[name] = appAuthProvider[name]
        newValues[name] = values[name]
      }
    })

    await dispatch('forceUpdate', {
      userSource,
      appAuthProvider,
      values: newValues,
    })

    return new Promise((resolve, reject) => {
      const fire = async () => {
        try {
          await AppAuthProviderService(this.$client).update(
            appAuthProvider.id,
            values
          )
          updateContext.lastUpdatedValues = values
          resolve()
        } catch (error) {
          // Revert to old values on error
          await dispatch('forceUpdate', {
            userSource,
            appAuthProvider,
            values: updateContext.lastUpdatedValues,
          })
          reject(error)
        }
      }

      if (updateContext.promiseResolve) {
        updateContext.promiseResolve()
        updateContext.promiseResolve = null
      }

      clearTimeout(updateContext.updateTimeout)

      if (!updateContext.lastUpdatedValues) {
        updateContext.lastUpdatedValues = oldValues
      }

      updateContext.updateTimeout = setTimeout(fire, 500)
      updateContext.promiseResolve = resolve
    })
  },
  async delete({ dispatch, getters }, { userSource, appAuthProviderId }) {
    const appAuthProvidersOfUserSource = getters.getUserSources(userSource)
    const appAuthProviderIndex = appAuthProvidersOfUserSource.findIndex(
      (appAuthProvider) => appAuthProvider.id === appAuthProviderId
    )
    const appAuthProviderToDelete =
      appAuthProvidersOfUserSource[appAuthProviderIndex]
    const beforeId =
      appAuthProviderIndex !== appAuthProvidersOfUserSource.length - 1
        ? appAuthProvidersOfUserSource[appAuthProviderIndex + 1].id
        : null

    await dispatch('forceDelete', { userSource, appAuthProviderId })

    try {
      await AppAuthProviderService(this.$client).delete(appAuthProviderId)
    } catch (error) {
      await dispatch('forceCreate', {
        userSource,
        appAuthProvider: appAuthProviderToDelete,
        beforeId,
      })
      throw error
    }
  },
}

const getters = {
  getAppAuthProviders: (state) => (userSource) => {
    return userSource.appAuthProviders
  },
}

export default {
  namespaced: true,
  state,
  getters,
  actions,
  mutations,
}

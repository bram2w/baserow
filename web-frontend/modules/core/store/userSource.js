import UserSourceService from '@baserow/modules/core/services/userSource'
import _ from 'lodash'

const state = {
  // The loaded userSources
  userSources: [],
}

const updateContext = {
  updateTimeout: null,
  promiseResolve: null,
  lastUpdatedValues: null,
}

const mutations = {
  ADD_ITEM(state, { userSource, beforeId = null }) {
    if (beforeId === null) {
      state.userSources.push(userSource)
    } else {
      const insertionIndex = state.userSources.findIndex(
        (e) => e.id === beforeId
      )
      state.userSources.splice(insertionIndex, 0, userSource)
    }
  },
  UPDATE_ITEM(state, { userSource: userSourceToUpdate, values }) {
    state.userSources.forEach((userSource) => {
      if (userSource.id === userSourceToUpdate.id) {
        Object.assign(userSource, values)
      }
    })
  },
  DELETE_ITEM(state, { userSourceId }) {
    const index = state.userSources.findIndex(
      (userSource) => userSource.id === userSourceId
    )
    if (index > -1) {
      state.userSources.splice(index, 1)
    }
  },
  MOVE_ITEM(state, { index, oldIndex }) {
    state.userSources.splice(index, 0, state.userSources.splice(oldIndex, 1)[0])
  },
  CLEAR_ITEMS(state) {
    state.userSources = []
  },
}

const actions = {
  forceCreate({ commit }, { userSource, beforeId = null }) {
    commit('ADD_ITEM', { userSource, beforeId })
  },
  forceUpdate({ commit }, { userSource, values }) {
    commit('UPDATE_ITEM', { userSource, values })
  },
  forceDelete({ commit, getters }, { userSourceId }) {
    commit('DELETE_ITEM', { userSourceId })
  },
  forceMove({ commit, getters }, { userSourceId, beforeUserSourceId }) {
    const currentOrder = getters.getUserSources.map(
      (userSource) => userSource.id
    )
    const oldIndex = currentOrder.findIndex((id) => id === userSourceId)
    const index = beforeUserSourceId
      ? currentOrder.findIndex((id) => id === beforeUserSourceId)
      : getters.getUserSources.length

    // If the userSource is before the beforeUserSource we must decrease the target index by
    // one to compensate the removed userSource.
    if (oldIndex < index) {
      commit('MOVE_ITEM', { index: index - 1, oldIndex })
    } else {
      commit('MOVE_ITEM', { index, oldIndex })
    }
  },
  async create(
    { dispatch },
    { applicationId, userSourceType, values, beforeId = null }
  ) {
    const { data: userSource } = await UserSourceService(this.$client).create(
      applicationId,
      userSourceType,
      values,
      beforeId
    )

    await dispatch('forceCreate', { userSource, beforeId })

    return userSource
  },
  async update({ dispatch, getters }, { userSourceId, values }) {
    const userSourcesOfPage = getters.getUserSources
    const userSource = userSourcesOfPage.find(({ id }) => id === userSourceId)

    const oldValues = {}
    const newValues = {}

    Object.keys(values).forEach((name) => {
      if (!_.isEqual(userSource[name], values[name])) {
        oldValues[name] = userSource[name]
        newValues[name] = values[name]
      }
    })

    await dispatch('forceUpdate', { userSource, values: newValues })

    try {
      const { data: newUserSource } = await UserSourceService(
        this.$client
      ).update(userSource.id, newValues)
      await dispatch('forceUpdate', { userSource, values: newUserSource })
    } catch (error) {
      await dispatch('forceUpdate', { userSource, values: oldValues })
      throw error
    }
  },

  async debouncedUpdate({ dispatch, getters }, { userSourceId, values }) {
    const userSource = getters.getUserSources.find(
      ({ id }) => id === userSourceId
    )
    const oldValues = {}
    const newValues = {}
    Object.keys(values).forEach((name) => {
      if (Object.prototype.hasOwnProperty.call(userSource, name)) {
        oldValues[name] = userSource[name]
        newValues[name] = values[name]
      }
    })

    await dispatch('forceUpdate', { userSource, values: newValues })

    return new Promise((resolve, reject) => {
      const fire = async () => {
        try {
          await UserSourceService(this.$client).update(userSource.id, values)
          updateContext.lastUpdatedValues = values
          resolve()
        } catch (error) {
          // Revert to old values on error
          await dispatch('forceUpdate', {
            userSource,
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
  async delete({ dispatch, getters }, { userSourceId }) {
    const userSourcesOfPage = getters.getUserSources
    const userSourceIndex = userSourcesOfPage.findIndex(
      (userSource) => userSource.id === userSourceId
    )
    const userSourceToDelete = userSourcesOfPage[userSourceIndex]
    const beforeId =
      userSourceIndex !== userSourcesOfPage.length - 1
        ? userSourcesOfPage[userSourceIndex + 1].id
        : null

    await dispatch('forceDelete', { userSourceId })

    try {
      await UserSourceService(this.$client).delete(userSourceId)
    } catch (error) {
      await dispatch('forceCreate', {
        userSource: userSourceToDelete,
        beforeId,
      })
      throw error
    }
  },
  async fetch({ dispatch, commit }, { applicationId }) {
    commit('CLEAR_ITEMS')

    const { data: userSources } = await UserSourceService(
      this.$client
    ).fetchAll(applicationId)

    await Promise.all(
      userSources.map((userSource) => dispatch('forceCreate', { userSource }))
    )

    return userSources
  },
  async move({ dispatch }, { userSourceId, beforeUserSourceId }) {
    await dispatch('forceMove', {
      userSourceId,
      beforeUserSourceId,
    })

    try {
      await UserSourceService(this.$client).move(
        userSourceId,
        beforeUserSourceId
      )
    } catch (error) {
      await dispatch('forceMove', {
        userSourceId: beforeUserSourceId,
        beforeUserSourceId: userSourceId,
      })
      throw error
    }
  },
  async duplicate({ getters, dispatch }, { userSourceId, applicationId }) {
    const userSource = getters.getUserSources.find((e) => e.id === userSourceId)
    await dispatch('create', {
      applicationId,
      userSourceType: userSource.type,
      beforeId: userSource.id,
    })
  },
}

const getters = {
  getUserSources: (state) => {
    return state.userSources
  },
}

export default {
  namespaced: true,
  state,
  getters,
  actions,
  mutations,
}

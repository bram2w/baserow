import IntegrationService from '@baserow/modules/core/services/integration'

const state = {
  // The loaded integrations
  integrations: [],
}

const updateContext = {
  updateTimeout: null,
  promiseResolve: null,
  lastUpdatedValues: null,
}

const mutations = {
  ADD_ITEM(state, { integration, beforeId = null }) {
    if (beforeId === null) {
      state.integrations.push(integration)
    } else {
      const insertionIndex = state.integrations.findIndex(
        (e) => e.id === beforeId
      )
      state.integrations.splice(insertionIndex, 0, integration)
    }
  },
  UPDATE_ITEM(state, { integration: integrationToUpdate, values }) {
    state.integrations.forEach((integration) => {
      if (integration.id === integrationToUpdate.id) {
        Object.assign(integration, values)
      }
    })
  },
  DELETE_ITEM(state, { integrationId }) {
    const index = state.integrations.findIndex(
      (integration) => integration.id === integrationId
    )
    if (index > -1) {
      state.integrations.splice(index, 1)
    }
  },
  MOVE_ITEM(state, { index, oldIndex }) {
    state.integrations.splice(
      index,
      0,
      state.integrations.splice(oldIndex, 1)[0]
    )
  },
  CLEAR_ITEMS(state) {
    state.integrations = []
  },
}

const actions = {
  forceCreate({ commit }, { integration, beforeId = null }) {
    commit('ADD_ITEM', { integration, beforeId })
  },
  forceUpdate({ commit }, { integration, values }) {
    commit('UPDATE_ITEM', { integration, values })
  },
  forceDelete({ commit, getters }, { integrationId }) {
    commit('DELETE_ITEM', { integrationId })
  },
  forceMove({ commit, getters }, { integrationId, beforeIntegrationId }) {
    const currentOrder = getters.getIntegrations.map(
      (integration) => integration.id
    )
    const oldIndex = currentOrder.findIndex((id) => id === integrationId)
    const index = beforeIntegrationId
      ? currentOrder.findIndex((id) => id === beforeIntegrationId)
      : getters.getIntegrations.length

    // If the integration is before the beforeIntegration we must decrease the target index by
    // one to compensate the removed integration.
    if (oldIndex < index) {
      commit('MOVE_ITEM', { index: index - 1, oldIndex })
    } else {
      commit('MOVE_ITEM', { index, oldIndex })
    }
  },
  async create(
    { dispatch },
    { applicationId, integrationType, values, beforeId = null }
  ) {
    const { data: integration } = await IntegrationService(this.$client).create(
      applicationId,
      integrationType,
      values,
      beforeId
    )

    await dispatch('forceCreate', { integration, beforeId })

    return integration
  },
  async update({ dispatch, getters }, { integrationId, values }) {
    const integrationsOfPage = getters.getIntegrations
    const integration = integrationsOfPage.find(
      ({ id }) => id === integrationId
    )
    const oldValues = {}
    const newValues = {}
    Object.keys(values).forEach((name) => {
      if (Object.prototype.hasOwnProperty.call(integration, name)) {
        oldValues[name] = integration[name]
        newValues[name] = values[name]
      }
    })

    await dispatch('forceUpdate', { integration, values: newValues })

    try {
      await IntegrationService(this.$client).update(integration.id, values)
    } catch (error) {
      await dispatch('forceUpdate', { integration, values: oldValues })
      throw error
    }
  },

  async debouncedUpdate({ dispatch, getters }, { integrationId, values }) {
    const integration = getters.getIntegrations.find(
      ({ id }) => id === integrationId
    )
    const oldValues = {}
    const newValues = {}
    Object.keys(values).forEach((name) => {
      if (Object.prototype.hasOwnProperty.call(integration, name)) {
        oldValues[name] = integration[name]
        newValues[name] = values[name]
      }
    })

    await dispatch('forceUpdate', { integration, values: newValues })

    return new Promise((resolve, reject) => {
      const fire = async () => {
        try {
          await IntegrationService(this.$client).update(integration.id, values)
          updateContext.lastUpdatedValues = values
          resolve()
        } catch (error) {
          // Revert to old values on error
          await dispatch('forceUpdate', {
            integration,
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
  async delete({ dispatch, getters }, { integrationId }) {
    const integrationsOfPage = getters.getIntegrations
    const integrationIndex = integrationsOfPage.findIndex(
      (integration) => integration.id === integrationId
    )
    const integrationToDelete = integrationsOfPage[integrationIndex]
    const beforeId =
      integrationIndex !== integrationsOfPage.length - 1
        ? integrationsOfPage[integrationIndex + 1].id
        : null

    await dispatch('forceDelete', { integrationId })

    try {
      await IntegrationService(this.$client).delete(integrationId)
    } catch (error) {
      await dispatch('forceCreate', {
        integration: integrationToDelete,
        beforeId,
      })
      throw error
    }
  },
  async fetch({ dispatch, commit }, { applicationId }) {
    commit('CLEAR_ITEMS')

    const { data: integrations } = await IntegrationService(
      this.$client
    ).fetchAll(applicationId)

    await Promise.all(
      integrations.map((integration) =>
        dispatch('forceCreate', { integration })
      )
    )

    return integrations
  },
  async move({ dispatch }, { integrationId, beforeIntegrationId }) {
    await dispatch('forceMove', {
      integrationId,
      beforeIntegrationId,
    })

    try {
      await IntegrationService(this.$client).move(
        integrationId,
        beforeIntegrationId
      )
    } catch (error) {
      await dispatch('forceMove', {
        integrationId: beforeIntegrationId,
        beforeIntegrationId: integrationId,
      })
      throw error
    }
  },
  async duplicate({ getters, dispatch }, { integrationId, applicationId }) {
    const integration = getters.getIntegrations.find(
      (e) => e.id === integrationId
    )
    await dispatch('create', {
      applicationId,
      integrationType: integration.type,
      beforeId: integration.id,
    })
  },
}

const getters = {
  getIntegrations: (state) => {
    return state.integrations
  },
  getIntegrationById: (state) => (id) => {
    return state.integrations.find((integration) => integration.id === id)
  },
}

export default {
  namespaced: true,
  state,
  getters,
  actions,
  mutations,
}

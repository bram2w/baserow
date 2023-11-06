import WorkflowActionService from '@baserow/modules/builder/services/workflowAction'
import PublishedBuilderService from '@baserow/modules/builder/services/publishedBuilder'

const updateContext = {
  updateTimeout: null,
  promiseResolve: null,
  lastUpdatedValues: null,
}

const state = {}

const mutations = {
  ADD_ITEM(state, { page, workflowAction }) {
    page.workflowActions.push(workflowAction)
  },
  SET_ITEMS(state, { page, workflowActions }) {
    page.workflowActions = workflowActions
  },
  DELETE_ITEM(state, { page, workflowActionId }) {
    const index = page.workflowActions.findIndex(
      (workflowAction) => workflowAction.id === workflowActionId
    )
    if (index > -1) {
      page.workflowActions.splice(index, 1)
    }
  },
  UPDATE_ITEM(state, { page, workflowAction: workflowActionToUpdate, values }) {
    page.workflowActions.forEach((workflowAction) => {
      if (workflowAction.id === workflowActionToUpdate.id) {
        Object.assign(workflowAction, values)
      }
    })
  },
  SET_ITEM(state, { page, workflowAction: workflowActionToSet, values }) {
    page.workflowActions = page.workflowActions.map((workflowAction) =>
      workflowAction.id === workflowActionToSet.id ? values : workflowAction
    )
  },
}

const actions = {
  forceCreate({ commit }, { page, workflowAction }) {
    commit('ADD_ITEM', { page, workflowAction })
  },
  forceDelete({ commit }, { page, workflowActionId }) {
    commit('DELETE_ITEM', { page, workflowActionId })
  },
  forceUpdate({ commit }, { page, workflowAction, values }) {
    commit('UPDATE_ITEM', { page, workflowAction, values })
  },
  forceSet({ commit }, { page, workflowAction, values }) {
    commit('SET_ITEM', { page, workflowAction, values })
  },
  async create(
    { dispatch },
    { page, workflowActionType, eventType, configuration = null }
  ) {
    const { data: workflowAction } = await WorkflowActionService(
      this.$client
    ).create(page.id, workflowActionType, eventType, configuration)

    await dispatch('forceCreate', { page, workflowAction })

    return workflowAction
  },
  async fetch({ commit }, { page }) {
    const { data: workflowActions } = await WorkflowActionService(
      this.$client
    ).fetchAll(page.id)

    commit('SET_ITEMS', { page, workflowActions })
  },
  async fetchPublished({ commit }, { page }) {
    const { data: workflowActions } = await PublishedBuilderService(
      this.$client
    ).fetchWorkflowActions(page.id)

    commit('SET_ITEMS', { page, workflowActions })
  },
  async delete({ dispatch }, { page, workflowAction }) {
    dispatch('forceDelete', { page, workflowActionId: workflowAction.id })

    try {
      await WorkflowActionService(this.$client).delete(workflowAction.id)
    } catch (error) {
      await dispatch('forceCreate', { page, workflowAction })
      throw error
    }
  },
  async update({ dispatch }, { page, workflowAction, values }) {
    const oldValues = {}
    const newValues = {}
    Object.keys(values).forEach((name) => {
      if (Object.prototype.hasOwnProperty.call(workflowAction, name)) {
        oldValues[name] = workflowAction[name]
        newValues[name] = values[name]
      }
    })

    await dispatch('forceUpdate', { page, workflowAction, values: newValues })

    try {
      const { data } = await WorkflowActionService(this.$client).update(
        workflowAction.id,
        values
      )
      await dispatch('forceSet', { page, workflowAction, values: data })
    } catch (error) {
      await dispatch('forceUpdate', { page, workflowAction, values: oldValues })
      throw error
    }
  },
  async updateDebounced({ dispatch }, { page, workflowAction, values }) {
    const oldValues = {}
    const newValues = {}
    Object.keys(values).forEach((name) => {
      if (Object.prototype.hasOwnProperty.call(workflowAction, name)) {
        oldValues[name] = workflowAction[name]
        newValues[name] = values[name]
      }
    })

    await dispatch('forceUpdate', { page, workflowAction, values: newValues })

    return new Promise((resolve, reject) => {
      const fire = async () => {
        try {
          const { data } = await WorkflowActionService(this.$client).update(
            workflowAction.id,
            values
          )
          await dispatch('forceSet', {
            page,
            workflowAction,
            values: data,
          })
          resolve()
        } catch (error) {
          await dispatch('forceUpdate', {
            page,
            workflowAction,
            values: updateContext.lastUpdatedValues,
          })
          reject(error)
        }
        updateContext.lastUpdatedValues = null
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
}

const getters = {
  getElementWorkflowActions: (state) => (page, elementId) => {
    return page.workflowActions.filter(
      (workflowAction) => workflowAction.element_id === elementId
    )
  },
}

export default {
  namespaced: true,
  state,
  mutations,
  actions,
  getters,
}

import DataSourceService from '@baserow/modules/builder/services/dataSource'

const state = {
  // The dataSources currently loaded
  dataSources: [],
}

const updateContext = {
  updateTimeout: null,
  promiseResolve: null,
  lastUpdatedValues: null,
}

const mutations = {
  ADD_ITEM(state, { dataSource, beforeId = null }) {
    if (beforeId === null) {
      state.dataSources.push(dataSource)
    } else {
      const insertionIndex = state.dataSources.findIndex(
        (e) => e.id === beforeId
      )
      state.dataSources.splice(insertionIndex, 0, dataSource)
    }
  },
  UPDATE_ITEM(state, { dataSource: dataSourceToUpdate, values }) {
    state.dataSources.forEach((dataSource) => {
      if (dataSource.id === dataSourceToUpdate.id) {
        Object.assign(dataSource, values)
      }
    })
  },
  DELETE_ITEM(state, { dataSourceId }) {
    const index = state.dataSources.findIndex(
      (dataSource) => dataSource.id === dataSourceId
    )
    if (index > -1) {
      state.dataSources.splice(index, 1)
    }
  },
  MOVE_ITEM(state, { index, oldIndex }) {
    state.dataSources.splice(index, 0, state.dataSources.splice(oldIndex, 1)[0])
  },
  CLEAR_ITEMS(state) {
    state.dataSources = []
  },
}

const actions = {
  forceCreate({ commit }, { dataSource, beforeId = null }) {
    commit('ADD_ITEM', { dataSource, beforeId })
  },
  forceUpdate({ commit }, { dataSource, values }) {
    commit('UPDATE_ITEM', { dataSource, values })
  },
  forceDelete({ commit }, { dataSourceId }) {
    commit('DELETE_ITEM', { dataSourceId })
  },
  forceMove({ commit, getters }, { dataSourceId, beforeDataSourceId }) {
    const currentOrder = getters.getDataSources.map(
      (dataSource) => dataSource.id
    )
    const oldIndex = currentOrder.findIndex((id) => id === dataSourceId)
    const index = beforeDataSourceId
      ? currentOrder.findIndex((id) => id === beforeDataSourceId)
      : getters.getDataSources.length

    // If the dataSource is before the beforeDataSource we must decrease the target index by
    // one to compensate the removed dataSource.
    if (oldIndex < index) {
      commit('MOVE_ITEM', { index: index - 1, oldIndex })
    } else {
      commit('MOVE_ITEM', { index, oldIndex })
    }
  },
  async create({ dispatch }, { pageId, values, beforeId }) {
    const { data: dataSource } = await DataSourceService(this.$client).create(
      pageId,
      values,
      beforeId
    )

    await dispatch('forceCreate', { dataSource, beforeId })
  },
  async update({ dispatch }, { dataSourceId, values }) {
    const dataSourcesOfPage = getters.getDataSources
    const dataSource = dataSourcesOfPage.find(
      (dataSource) => dataSource.id === dataSourceId
    )
    const oldValues = {}
    const newValues = {}
    Object.keys(values).forEach((name) => {
      if (Object.prototype.hasOwnProperty.call(dataSource, name)) {
        oldValues[name] = dataSource[name]
        newValues[name] = values[name]
      }
    })

    await dispatch('forceUpdate', { dataSource, values: newValues })

    try {
      await DataSourceService(this.$client).update(dataSource.id, values)
    } catch (error) {
      await dispatch('forceUpdate', { dataSource, values: oldValues })
      throw error
    }
  },

  async debouncedUpdate({ dispatch, getters }, { dataSourceId, values }) {
    const dataSourcesOfPage = getters.getDataSources
    const dataSource = dataSourcesOfPage.find(
      (dataSource) => dataSource.id === dataSourceId
    )
    const oldValues = {}
    const newValues = {}
    Object.keys(values).forEach((name) => {
      if (Object.prototype.hasOwnProperty.call(dataSource, name)) {
        oldValues[name] = dataSource[name]
        newValues[name] = values[name]
      }
    })

    await dispatch('forceUpdate', { dataSource, values: newValues })

    return new Promise((resolve, reject) => {
      const fire = async () => {
        try {
          await DataSourceService(this.$client).update(dataSource.id, values)
          resolve()
        } catch (error) {
          // Revert to old values on error

          await dispatch('forceUpdate', {
            dataSource,
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
  async delete({ dispatch, getters }, { dataSourceId }) {
    const dataSourcesOfPage = getters.getDataSources
    const dataSourceIndex = dataSourcesOfPage.findIndex(
      (dataSource) => dataSource.id === dataSourceId
    )
    const dataSourceToDelete = dataSourcesOfPage[dataSourceIndex]
    const beforeId =
      dataSourceIndex !== dataSourcesOfPage.length - 1
        ? dataSourcesOfPage[dataSourceIndex + 1].id
        : null

    await dispatch('forceDelete', { dataSourceId })

    try {
      await DataSourceService(this.$client).delete(dataSourceId)
    } catch (error) {
      await dispatch('forceCreate', {
        dataSource: dataSourceToDelete,
        beforeId,
      })
      throw error
    }
  },
  async fetch({ dispatch, commit }, { page }) {
    commit('CLEAR_ITEMS')

    const { data: dataSources } = await DataSourceService(
      this.$client
    ).fetchAll(page.id)

    await Promise.all(
      dataSources.map((dataSource) => dispatch('forceCreate', { dataSource }))
    )

    return dataSources
  },
  async move({ dispatch }, { dataSourceId, beforeDataSourceId }) {
    await dispatch('forceMove', {
      dataSourceId,
      beforeDataSourceId,
    })

    try {
      await DataSourceService(this.$client).move(
        dataSourceId,
        beforeDataSourceId
      )
    } catch (error) {
      await dispatch('forceMove', {
        dataSourceId: beforeDataSourceId,
        beforeDataSourceId: dataSourceId,
      })
      throw error
    }
  },
  async duplicate({ getters, dispatch }, { dataSourceId, pageId }) {
    const dataSource = getters.getDataSources.find((e) => e.id === dataSourceId)
    await dispatch('create', {
      pageId,
      dataSourceType: dataSource.type,
      beforeId: dataSource.id,
    })
  },
}

const getters = {
  getDataSources: (state) => {
    return state.dataSources
  },
}

export default {
  namespaced: true,
  state,
  getters,
  actions,
  mutations,
}

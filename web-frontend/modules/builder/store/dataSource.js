import DataSourceService from '@baserow/modules/builder/services/dataSource'
import PublishedBuilderService from '@baserow/modules/builder/services/publishedBuilder'

const state = {
  // The dataSources currently loaded
  dataSources: [],
}

const updateContext = {
  updateTimeout: null,
  promiseResolve: null,
  lastUpdatedValues: null,
  valuesToUpdate: {},
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
    const index = state.dataSources.findIndex(
      (dataSource) => dataSource.id === dataSourceToUpdate.id
    )
    state.dataSources.splice(index, 1, {
      ...state.dataSources[index],
      ...values,
    })
  },
  FULL_UPDATE_ITEM(state, { dataSource: dataSourceToUpdate, values }) {
    const index = state.dataSources.findIndex(
      (dataSource) => dataSource.id === dataSourceToUpdate.id
    )
    state.dataSources.splice(index, 1, {
      ...values,
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

  debouncedUpdate({ dispatch, getters, commit }, { dataSourceId, values }) {
    const dataSourcesOfPage = getters.getDataSources
    const dataSource = dataSourcesOfPage.find(
      (dataSource) => dataSource.id === dataSourceId
    )
    const oldValues = {}
    Object.keys(values).forEach((name) => {
      if (Object.prototype.hasOwnProperty.call(dataSource, name)) {
        oldValues[name] = dataSource[name]
        // Accumulate the changed values to send all the ongoing changes with the
        // final request
        updateContext.valuesToUpdate[name] = values[name]
      }
    })

    return new Promise((resolve, reject) => {
      const fire = async () => {
        try {
          const { data } = await DataSourceService(this.$client).update(
            dataSource.id,
            updateContext.valuesToUpdate
          )
          await commit('FULL_UPDATE_ITEM', { dataSource, values: data })
          resolve()
        } catch (error) {
          // Revert to old values on error
          await dispatch('forceUpdate', {
            dataSource,
            values: updateContext.lastUpdatedValues,
          })
          reject(error)
        }
        updateContext.valuesToUpdate = {}
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
    dispatch('dataSourceContent/clearDataSourceContents', null, { root: true })
    const { data: dataSources } = await DataSourceService(
      this.$client
    ).fetchAll(page.id)

    commit('CLEAR_ITEMS')
    await Promise.all(
      dataSources.map((dataSource) => dispatch('forceCreate', { dataSource }))
    )

    return dataSources
  },
  async fetchPublished({ dispatch, commit }, { page }) {
    dispatch('dataSourceContent/clearDataSourceContents', null, { root: true })

    const { data: dataSources } = await PublishedBuilderService(
      this.$client
    ).fetchDataSources(page.id)

    commit('CLEAR_ITEMS')
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

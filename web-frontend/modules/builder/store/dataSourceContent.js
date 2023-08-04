import _ from 'lodash'
import DataSourceService from '@baserow/modules/builder/services/dataSource'
import { clone } from '@baserow/modules/core/utils/object'

const state = {
  // The data source loaded content.
  contents: {},
  // Save the fetch content status
  fetchContext: {},
}

const fetchTimeout = {}

const mutations = {
  SET_CONTENT(state, { dataSourceId, value }) {
    if (!state.contents[dataSourceId]) {
      // Here we need to change the reference of the dataSourceContents object to
      // trigger computed values that use it in some situation (before the key exists
      // for instance)
      state.contents = {
        ...state.contents,
        [dataSourceId]: value,
      }
    } else if (!_.isEqual(state.contents[dataSourceId], value)) {
      state.contents[dataSourceId] = value
    }
  },
  UPDATE_FETCH_CONTEXT(state, { dataSourceId, value }) {
    if (!state.fetchContext[dataSourceId]) {
      // Here we need to change the reference of the dataSourceContents object to
      // trigger computed values that use it in some situation (before the key exists
      // for instance)
      state.fetchContext = {
        ...state.fetchContext,
        [dataSourceId]: { lastDataSource: null, lastQueryData: null, ...value },
      }
    } else if (!_.isEqual(state.fetchContext[dataSourceId], value)) {
      state.fetchContext[dataSourceId] = value
    }
  },
  CLEAR_CONTENTS(state) {
    state.contents = {}
    state.fetchContext = {}
  },
}

const actions = {
  /**
   * Fetch the data from the server and add them to the store.
   * @param {object} dataSource the data source we want to dispatch
   * @param {object} data the query body
   */
  async fetchDataSourceContent({ commit }, { dataSource, data: queryData }) {
    if (!dataSource.type) {
      return
    }

    const serviceType = this.app.$registry.get('service', dataSource.type)

    try {
      if (serviceType.isValid(dataSource)) {
        const { data } = await DataSourceService(this.app.$client).dispatch(
          dataSource.id,
          queryData
        )
        commit('SET_CONTENT', { dataSourceId: dataSource.id, value: data })
      } else {
        commit('SET_CONTENT', { dataSourceId: dataSource.id, value: null })
      }
    } catch (e) {
      commit('SET_CONTENT', { dataSourceId: dataSource.id, value: null })
    } finally {
      commit('UPDATE_FETCH_CONTEXT', {
        dataSourceId: dataSource.id,
        value: {
          lastDataSource: clone(dataSource),
          lastQueryData: clone(queryData),
        },
      })
    }
  },

  async fetchPageDataSourceContent(
    { commit },
    { page, data: queryData, dataSources }
  ) {
    try {
      const { data } = await DataSourceService(this.app.$client).dispatchAll(
        page.id,
        queryData
      )

      Object.entries(data).forEach(([dataSourceIdStr, dataContent]) => {
        const dataSourceId = parseInt(dataSourceIdStr, 10)
        const foundDataSource = dataSources.find(
          ({ id }) => id === dataSourceId
        )
        // if we don't find the data source it means it's not fully configured
        if (foundDataSource !== undefined) {
          commit('UPDATE_FETCH_CONTEXT', {
            dataSourceId,
            value: {
              lastDataSource: clone(foundDataSource),
              lastQueryData: clone(queryData),
            },
          })
          if (dataContent._error) {
            commit('SET_CONTENT', { dataSourceId, value: null })
          } else {
            commit('SET_CONTENT', { dataSourceId, value: dataContent })
          }
        }
      })
    } catch (e) {
      commit('CLEAR_CONTENTS')
      throw e
    }
  },

  /**
   * Fetches the data from the server and add them to the store only when needed.
   * It's necessary when it's the first call (the store is empty) and when the
   * configuration or the body content has changed.
   * @param {object} dataSource the data source we want to dispatch
   * @param {object} data the query body
   */
  smartFetchDataSourceContent(
    { dispatch, getters },
    { dataSource, data: queryData }
  ) {
    const fetch = async () => {
      const { lastDataSource = null, lastQueryData = null } =
        getters.getFetchContext[dataSource.id] || {}
      // We want to update the content only if the dataSource configuration or the query
      // parameters have changed.
      if (
        !_.isEqual(lastDataSource, dataSource) ||
        !_.isEqual(lastQueryData, queryData)
      ) {
        await dispatch('fetchDataSourceContent', {
          dataSource,
          data: queryData,
        })
      }
    }

    // Then subsequent calls are debounced by 500ms
    clearTimeout(fetchTimeout[dataSource.id])
    fetchTimeout[dataSource.id] = setTimeout(fetch, 500)
  },

  clearDataSourceContents({ commit }) {
    commit('CLEAR_CONTENTS')
  },
}

const getters = {
  getDataSourceContents: (state) => {
    return state.contents
  },
  getFetchContext: (state) => {
    return state.fetchContext
  },
}

export default {
  namespaced: true,
  state,
  getters,
  actions,
  mutations,
}

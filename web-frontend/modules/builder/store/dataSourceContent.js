import _ from 'lodash'
import Vue from 'vue'
import DataSourceService from '@baserow/modules/builder/services/dataSource'

const state = {}

let pageFetchTimeout = null

const mutations = {
  SET_CONTENT(state, { page, dataSourceId, value }) {
    if (!page.contents) {
      Vue.set(page, 'contents', {})
    }

    if (!_.isEqual(page.contents[dataSourceId], value)) {
      // Here we need to change the reference of the dataSourceContents object to
      // trigger computed values that use it in some situation (before the key exists
      // for instance)
      page.contents = {
        ...page.contents,
        [dataSourceId]: value,
      }
    }
  },
  CLEAR_CONTENTS(state, { page }) {
    Vue.set(page, 'contents', {})
  },
  SET_LOADING(state, { page, value }) {
    page._.dataSourceContentLoading = value
  },
}

const actions = {
  /**
   * Fetch the content for every data sources of the given page.
   */
  async fetchPageDataSourceContent({ commit }, { page, data: queryData }) {
    commit('SET_LOADING', { page, value: true })
    try {
      const { data } = await DataSourceService(this.app.$client).dispatchAll(
        page.id,
        queryData
      )

      Object.entries(data).forEach(([dataSourceIdStr, dataContent]) => {
        const dataSourceId = parseInt(dataSourceIdStr, 10)
        if (dataContent._error) {
          commit('SET_CONTENT', { page, dataSourceId, value: null })
        } else {
          commit('SET_CONTENT', { page, dataSourceId, value: dataContent })
        }
      })
    } catch (e) {
      commit('CLEAR_CONTENTS', { page })
      throw e
    }
    commit('SET_LOADING', { page, value: false })
  },

  debouncedFetchPageDataSourceContent({ dispatch }, { page, data: queryData }) {
    clearTimeout(pageFetchTimeout)
    pageFetchTimeout = setTimeout(() => {
      dispatch('fetchPageDataSourceContent', {
        page,
        data: queryData,
      })
    }, 500)
  },

  clearDataSourceContent({ commit }, { page, dataSourceId }) {
    commit('SET_CONTENT', { page, dataSourceId, value: null })
  },

  clearDataSourceContents({ commit }, { page }) {
    commit('CLEAR_CONTENTS', { page })
  },
}

const getters = {
  getDataSourceContents: (state) => (page) => {
    return page.contents || {}
  },
  getLoading: (state) => (page) => {
    return page._.dataSourceContentLoading
  },
}

export default {
  namespaced: true,
  state,
  getters,
  actions,
  mutations,
}

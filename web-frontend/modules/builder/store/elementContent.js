import DataSourceService from '@baserow/modules/builder/services/dataSource'
import { rangeDiff } from '@baserow/modules/core/utils/range'

const state = {}

const mutations = {
  SET_CONTENT(state, { element, value, range }) {
    const [offset] = range
    const missingIndexes = offset + value.length - element._.content.length

    let newContent

    if (missingIndexes > 0) {
      newContent = element._.content.concat(Array(missingIndexes).fill(null))
    } else {
      newContent = [...element._.content]
    }

    value.forEach((record, index) => {
      newContent[offset + index] = record
    })

    element._.content = newContent
  },
  SET_HAS_MORE_PAGE(state, { element, value }) {
    element._.hasNextPage = value
  },

  CLEAR_CONTENT(state, { element }) {
    element._.content = []
    element._.hasNextPage = false
  },
  TRIGGER_RESET(state, { element }) {
    element._.reset += 1
  },
  SET_LOADING(state, { element, value }) {
    element._.contentLoading = value
  },
}

const actions = {
  /**
   * Fetch the data from the server and add them to the element store.
   * @param {object} dataSource the data source we want to dispatch
   * @param {object} data the query body
   */
  async fetchElementContent(
    { commit, getters },
    { element, dataSource, range, data: dispatchContext, replace = false }
  ) {
    if (!dataSource?.type) {
      return
    }

    const serviceType = this.app.$registry.get('service', dataSource.type)

    commit('SET_LOADING', { element, value: true })

    try {
      if (serviceType.isValid(dataSource)) {
        let rangeToFetch = range
        if (!replace) {
          // Let's compute the range that really needs to be fetched if necessary
          const [offset, count] = range
          rangeToFetch = rangeDiff(getters.getContentRange(element), [
            offset,
            offset + count,
          ])

          // Everything is already loaded we can quit now
          if (!rangeToFetch) {
            return
          }
          rangeToFetch = [rangeToFetch[0], rangeToFetch[1] - rangeToFetch[0]]
        }

        const response = await DataSourceService(this.app.$client).dispatch(
          dataSource.id,
          dispatchContext,
          { range: rangeToFetch }
        )

        const results = serviceType.returnsList
          ? response.data.results
          : [response.data]

        const hasNextPage =
          serviceType.returnsList && response.data.has_next_page
        if (replace) {
          commit('CLEAR_CONTENT', {
            element,
          })
        }
        commit('SET_CONTENT', {
          element,
          value: results,
          range,
        })
        commit('SET_HAS_MORE_PAGE', {
          element,
          value: hasNextPage,
        })
      } else {
        commit('CLEAR_CONTENT', {
          element,
        })
      }
    } catch (e) {
      // If fetching the content failed, and we're trying to
      // replace the element's content, then we'll clear the
      // element instead of reverting to our previousContent
      // as it could be out of date anyway.
      if (replace) {
        commit('CLEAR_CONTENT', { element })
      }
      throw e
    } finally {
      commit('SET_LOADING', { element, value: false })
    }
  },
  clearElementContent({ commit }, { element }) {
    commit('CLEAR_CONTENT', { element })
  },

  triggerElementContentReset({ commit }, { element }) {
    commit('TRIGGER_RESET', { element })
  },
}

const getters = {
  getElementContent: (state) => (element) => {
    return element._.content
  },
  getHasMorePage: (state) => (element) => {
    return element._.hasNextPage
  },
  getLoading: (state) => (element) => {
    return element._.contentLoading
  },
  getReset: (state) => (element) => {
    return element._.reset
  },
  getContentRange: (state) => (element) => {
    return [0, element._.content.length]
  },
}

export default {
  namespaced: true,
  state,
  getters,
  actions,
  mutations,
}

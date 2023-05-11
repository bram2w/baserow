import PublishedDomainService from '@baserow/modules/builder/services/publishedDomain'

const state = {
  // The public builder loaded
  builder: null,
}

const mutations = {
  SET_ITEM(state, { builder }) {
    state.builder = builder
  },
  CLEAR_ITEM(state) {
    state.builder = null
  },
}

const actions = {
  async fetchById({ commit }, { builderId }) {
    commit('CLEAR_ITEM')

    const { data } = await PublishedDomainService(this.$client).fetchById(
      builderId
    )
    commit('SET_ITEM', { builder: data })
  },

  async fetchByDomain({ commit }, { domain }) {
    commit('CLEAR_ITEM')

    const { data } = await PublishedDomainService(this.$client).fetchByDomain(
      domain
    )
    commit('SET_ITEM', { builder: data })
  },
}

const getters = {
  getBuilder: (state) => {
    return state.builder
  },
}

export default {
  namespaced: true,
  state,
  getters,
  actions,
  mutations,
}

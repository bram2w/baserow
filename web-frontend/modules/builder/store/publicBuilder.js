import PublishedBuilderService from '@baserow/modules/builder/services/publishedBuilder'

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

    const { data } = await PublishedBuilderService(this.$client).fetchById(
      builderId
    )
    commit('SET_ITEM', { builder: data })
  },

  async fetchByDomain({ commit }, { domain }) {
    commit('CLEAR_ITEM')

    const { data } = await PublishedBuilderService(this.$client).fetchByDomain(
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

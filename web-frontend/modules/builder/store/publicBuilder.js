import PublishedBuilderService from '@baserow/modules/builder/services/publishedBuilder'

const state = {}

const mutations = {}

const actions = {
  async fetchById({ dispatch }, { builderId }) {
    const { data } = await PublishedBuilderService(this.$client).fetchById(
      builderId
    )

    return await dispatch('application/forceCreate', data, { root: true })
  },

  async fetchByDomain({ dispatch }, { domain }) {
    const { data } = await PublishedBuilderService(this.$client).fetchByDomain(
      domain
    )

    return await dispatch('application/forceCreate', data, { root: true })
  },
}

const getters = {}

export default {
  namespaced: true,
  state,
  getters,
  actions,
  mutations,
}

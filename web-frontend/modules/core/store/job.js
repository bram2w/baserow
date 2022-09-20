export function populateJob(job, registry) {
  const type = registry.get('job', job.type)
  return type.populate(job)
}

export const state = () => ({
  items: [],
})

export const mutations = {
  ADD_ITEM(state, item) {
    state.items.push(item)
  },
  UPDATE_ITEM(state, { id, values }) {
    const index = state.items.findIndex((item) => item.id === id)
    if (index !== -1) {
      Object.assign(state.items[index], state.items[index], values)
    }
  },
  DELETE_ITEM(state, id) {
    const index = state.items.findIndex((item) => item.id === id)
    if (index !== -1) {
      state.items.splice(index, 1)
    }
  },
}

export const actions = {
  /**
   * Forcefully create an item in the store without making a call to the server.
   */
  forceCreate({ commit }, job) {
    populateJob(job, this.$registry)
    commit('ADD_ITEM', job)
  },
  /**
   * Forcefully update an item in the store without making a call to the server.
   */
  async forceUpdate({ commit }, { job, data }) {
    const type = this.$registry.get('job', job.type)
    await type.beforeUpdate(job, data)
    commit('UPDATE_ITEM', { id: job.id, values: data })
    await type.afterUpdate(job, data)
  },
  /**
   * Forcefully delete an item in the store without making a call to the server.
   */
  forceDelete({ commit }, job) {
    const type = this.$registry.get('job', job.type)
    type.beforeDelete(job, this)
    commit('DELETE_ITEM', job.id)
  },
  /**
   * Deletes all the jobs belonging to the given group.
   */
  deleteForGroup({ commit, state }, group) {
    const jobs = state.items.filter((job) =>
      this.$registry.get('job', job.type).isJobPartOfGroup(job, group)
    )
    jobs.forEach((job) => commit('DELETE_ITEM', job.id))
  },
  /**
   * Deletes all the jobs belonging to the given application.
   */
  deleteForApplication({ commit, state }, application) {
    const jobs = state.items.filter((job) =>
      this.$registry
        .get('job', job.type)
        .isJobPartOfApplication(job, application)
    )
    jobs.forEach((job) => commit('DELETE_ITEM', job.id))
  },
}

export const getters = {
  get: (state) => (id) => {
    return state.items.find((item) => item.id === id)
  },
  getAll: (state) => {
    return state.items
  },
}

export default {
  namespaced: true,
  state,
  getters,
  actions,
  mutations,
}

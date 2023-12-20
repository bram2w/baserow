import Vue from 'vue'

const state = {}

const mutations = {
  SET_FORM_DATA(state, { page, elementId, payload }) {
    if (!page.formData) {
      Vue.set(page, 'formData', {})
    }

    page.formData = { ...page.formData, [elementId]: payload }
  },
  REMOVE_FORM_DATA(state, { page, elementId }) {
    delete page.formData[elementId]
  },
}

const actions = {
  setFormData({ commit }, { page, elementId, payload }) {
    commit('SET_FORM_DATA', { page, elementId, payload })
  },
  removeFormData({ commit }, { page, elementId }) {
    commit('REMOVE_FORM_DATA', { page, elementId })
  },
}

const getters = {
  getFormData: (state) => (page) => {
    return page.formData || {}
  },
}

export default {
  namespaced: true,
  state,
  actions,
  getters,
  mutations,
}

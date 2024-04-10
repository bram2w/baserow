import Vue from 'vue'

const state = {}

const mutations = {
  SET_FORM_DATA(state, { page, elementId, payload }) {
    if (!page.formData) {
      Vue.set(page, 'formData', {})
    }

    // When the payload is being initialized, if it
    // doesn't have a 'touched' property, we set it to false
    if (!Object.prototype.hasOwnProperty.call(payload, 'touched')) {
      payload.touched = false
    }

    page.formData = { ...page.formData, [elementId]: payload }
  },
  REMOVE_FORM_DATA(state, { page, elementId }) {
    page.formData = Object.fromEntries(
      Object.entries(page.formData).filter(
        ([key]) => key !== elementId.toString()
      )
    )
  },
  SET_ELEMENT_TOUCHED(state, { page, elementId, wasTouched }) {
    page.formData[elementId].touched = wasTouched
  },
}

const actions = {
  setFormData({ commit }, { page, elementId, payload }) {
    commit('SET_FORM_DATA', { page, elementId, payload })
  },
  removeFormData({ commit }, { page, elementId }) {
    commit('REMOVE_FORM_DATA', { page, elementId })
  },
  setElementTouched({ commit }, { page, elementId, wasTouched }) {
    commit('SET_ELEMENT_TOUCHED', { page, elementId, wasTouched })
  },
}

const getters = {
  getFormData: (state) => (page) => {
    return page.formData || {}
  },
  getElementTouched: (state, getters) => (page, elementId) => {
    return page.formData[elementId].touched
  },
}

export default {
  namespaced: true,
  state,
  actions,
  getters,
  mutations,
}

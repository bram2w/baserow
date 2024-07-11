import Vue from 'vue'
import {
  getValueAtPath,
  setValueAtPath,
} from '@baserow/modules/core/utils/object'

const state = {}

/**
 * Responsible for setting a form entry at a given path in the form data of a page.
 * We use lodash's `set` in `setValueAtPath`. A shallow copy of `page.formData` is
 * returned with the updated value.
 * @param {Object} page - The page object that holds the form data.
 * @param {String} uniqueElementId - The unique element id of the form element.
 * @param {Any} value - The value to set at the path.
 */
function setFormEntryAtPath(page, uniqueElementId, value) {
  page.formData = setValueAtPath({ ...page.formData }, uniqueElementId, value)
}

const mutations = {
  SET_FORM_DATA(state, { page, uniqueElementId, payload }) {
    if (!page.formData) {
      Vue.set(page, 'formData', {})
    }
    setFormEntryAtPath(page, uniqueElementId, payload)
  },
  REMOVE_FORM_DATA(state, { page, elementId }) {
    page.formData = Object.fromEntries(
      Object.entries(page.formData).filter(
        ([key]) => key !== elementId.toString()
      )
    )
  },
  SET_ELEMENT_TOUCHED(state, { page, uniqueElementId, wasTouched }) {
    setFormEntryAtPath(page, `${uniqueElementId}.touched`, wasTouched)
  },
}

const actions = {
  setFormData({ commit }, { page, uniqueElementId, payload }) {
    commit('SET_FORM_DATA', { page, uniqueElementId, payload })
  },
  removeFormData({ commit }, { page, elementId }) {
    commit('REMOVE_FORM_DATA', { page, elementId })
  },
  setElementTouched({ commit }, { page, uniqueElementId, wasTouched }) {
    commit('SET_ELEMENT_TOUCHED', { page, uniqueElementId, wasTouched })
  },
}

const getters = {
  getFormData: (state) => (page) => {
    return page.formData || {}
  },
  getElementFormEntry: (state, getters) => (page, uniqueElementId) => {
    const formData = getters.getFormData(page)
    return getValueAtPath(formData, uniqueElementId) || {}
  },
  getElementInvalid: (state, getters) => (page, uniqueElementId) => {
    return !getters.getElementFormEntry(page, uniqueElementId).isValid
  },
  getElementTouched: (state, getters) => (page, uniqueElementId) => {
    return getters.getElementFormEntry(page, uniqueElementId).touched
  },
}

export default {
  namespaced: true,
  state,
  actions,
  getters,
  mutations,
}

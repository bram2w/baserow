import ElementService from '@baserow/modules/builder/services/element'
import PublicBuilderService from '@baserow/modules/builder/services/publishedBuilder'

const state = {
  // The elements of the currently selected page
  elements: [],

  // The currently selected element
  selected: null,
}

const updateContext = {
  updateTimeout: null,
  promiseResolve: null,
  lastUpdatedValues: null,
}

const mutations = {
  SET_ITEMS(state, { elements }) {
    state.selected = null
    state.elements = elements
  },
  ADD_ITEM(state, { element, beforeId = null }) {
    if (beforeId === null) {
      state.elements.push(element)
    } else {
      const insertionIndex = state.elements.findIndex((e) => e.id === beforeId)
      state.elements.splice(insertionIndex, 0, element)
    }
  },
  UPDATE_ITEM(state, { element: elementToUpdate, values }) {
    state.elements.forEach((element) => {
      if (element.id === elementToUpdate.id) {
        Object.assign(element, values)
      }
    })
  },
  DELETE_ITEM(state, { elementId }) {
    const index = state.elements.findIndex(
      (element) => element.id === elementId
    )
    if (index > -1) {
      state.elements.splice(index, 1)
    }
  },
  MOVE_ITEM(state, { index, oldIndex }) {
    state.elements.splice(index, 0, state.elements.splice(oldIndex, 1)[0])
  },
  SELECT_ITEM(state, { element }) {
    state.selected = element
  },
  CLEAR_ITEMS(state) {
    state.elements = []
  },
}

const actions = {
  clearAll({ commit }) {
    commit('CLEAR_ITEMS')
  },
  forceCreate({ commit }, { element, beforeId = null }) {
    commit('ADD_ITEM', { element, beforeId })
  },
  forceUpdate({ commit }, { element, values }) {
    commit('UPDATE_ITEM', { element, values })
  },
  forceDelete({ commit, getters }, { elementId }) {
    if (getters.getSelected.id === elementId) {
      commit('SELECT_ITEM', { element: null })
    }
    commit('DELETE_ITEM', { elementId })
  },
  forceMove({ commit, getters }, { elementId, beforeElementId }) {
    const currentOrder = getters.getElements.map((element) => element.id)
    const oldIndex = currentOrder.findIndex((id) => id === elementId)
    const index = beforeElementId
      ? currentOrder.findIndex((id) => id === beforeElementId)
      : getters.getElements.length

    // If the element is before the beforeElement we must decrease the target index by
    // one to compensate the removed element.
    if (oldIndex < index) {
      commit('MOVE_ITEM', { index: index - 1, oldIndex })
    } else {
      commit('MOVE_ITEM', { index, oldIndex })
    }
  },
  select({ commit }, { element }) {
    updateContext.lastUpdatedValues = null
    commit('SELECT_ITEM', { element })
  },
  async create(
    { dispatch },
    { pageId, elementType, beforeId = null, configuration = null }
  ) {
    const { data: element } = await ElementService(this.$client).create(
      pageId,
      elementType,
      beforeId,
      configuration
    )

    await dispatch('forceCreate', { element, beforeId })
  },
  async update({ dispatch }, { element, values }) {
    const elementType = this.$registry.get('element', element.type)
    const oldValues = {}
    const newValues = {}
    Object.keys(values).forEach((name) => {
      if (Object.prototype.hasOwnProperty.call(element, name)) {
        oldValues[name] = element[name]
        newValues[name] = values[name]
      }
    })

    await dispatch('forceUpdate', { element, values: newValues })

    try {
      await ElementService(this.$client).update(
        element.id,
        elementType.prepareValuesForRequest(values)
      )
    } catch (error) {
      await dispatch('forceUpdate', { element, values: oldValues })
      throw error
    }
  },

  async debouncedUpdateSelected({ dispatch, getters }, { values }) {
    const element = getters.getSelected
    const elementType = this.$registry.get('element', element.type)
    const oldValues = {}
    const newValues = {}
    Object.keys(values).forEach((name) => {
      if (Object.prototype.hasOwnProperty.call(element, name)) {
        oldValues[name] = element[name]
        newValues[name] = values[name]
      }
    })

    await dispatch('forceUpdate', { element, values: newValues })

    return new Promise((resolve, reject) => {
      const fire = async () => {
        try {
          await ElementService(this.$client).update(
            element.id,
            elementType.prepareValuesForRequest(values)
          )
          resolve()
        } catch (error) {
          // Revert to old values on error
          await dispatch('forceUpdate', {
            element,
            values: updateContext.lastUpdatedValues,
          })
          reject(error)
        }
        updateContext.lastUpdatedValues = null
      }

      if (updateContext.promiseResolve) {
        updateContext.promiseResolve()
        updateContext.promiseResolve = null
      }

      clearTimeout(updateContext.updateTimeout)

      if (!updateContext.lastUpdatedValues) {
        updateContext.lastUpdatedValues = oldValues
      }

      updateContext.updateTimeout = setTimeout(fire, 500)
      updateContext.promiseResolve = resolve
    })
  },
  async delete({ dispatch, getters }, { elementId }) {
    const elementsOfPage = getters.getElements
    const elementIndex = elementsOfPage.findIndex(
      (element) => element.id === elementId
    )
    const elementToDelete = elementsOfPage[elementIndex]
    const beforeId =
      elementIndex !== elementsOfPage.length - 1
        ? elementsOfPage[elementIndex + 1].id
        : null

    await dispatch('forceDelete', { elementId })

    try {
      await ElementService(this.$client).delete(elementId)
    } catch (error) {
      await dispatch('forceCreate', {
        element: elementToDelete,
        beforeId,
      })
      throw error
    }
  },
  async fetch({ commit }, { page }) {
    const { data: elements } = await ElementService(this.$client).fetchAll(
      page.id
    )

    commit('SET_ITEMS', { elements })

    return elements
  },
  async fetchPublished({ commit }, { page }) {
    const { data: elements } = await PublicBuilderService(
      this.$client
    ).fetchElements(page)

    commit('SET_ITEMS', { elements })

    return elements
  },
  async move({ dispatch }, { elementId, beforeElementId }) {
    await dispatch('forceMove', {
      elementId,
      beforeElementId,
    })

    try {
      await ElementService(this.$client).move(elementId, beforeElementId)
    } catch (error) {
      await dispatch('forceMove', {
        elementId: beforeElementId,
        beforeElementId: elementId,
      })
      throw error
    }
  },
  async duplicate({ getters, dispatch }, { elementId, pageId }) {
    const element = getters.getElements.find((e) => e.id === elementId)
    await dispatch('create', {
      pageId,
      beforeId: element.id,
      elementType: element.type,
      configuration: element,
    })
  },
}

const getters = {
  getElements: (state) => {
    return state.elements
  },
  getSelected(state) {
    return state.selected
  },
}

export default {
  namespaced: true,
  state,
  getters,
  actions,
  mutations,
}

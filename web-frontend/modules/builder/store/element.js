import ElementService from '@baserow/modules/builder/services/element'

const state = {
  // The elements of the currently selected page
  elements: [],

  // The currently selected element
  selected: null,
}

const mutations = {
  ADD_ITEM(state, { element, beforeId = null }) {
    if (beforeId === null) {
      state.elements.push(element)
    } else {
      const insertionIndex = state.elements.findIndex((e) => e.id === beforeId)
      state.elements.splice(insertionIndex, 0, element)
    }
  },
  DELETE_ITEM(state, { elementId }) {
    const index = state.elements.findIndex(
      (element) => element.id === elementId
    )
    state.elements.splice(index, 1)
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
  forceCreate({ commit }, { element, beforeId = null }) {
    commit('ADD_ITEM', { element, beforeId })
  },
  forceDelete({ commit }, { elementId }) {
    commit('DELETE_ITEM', { elementId })
  },
  forceMove({ commit }, { index, oldIndex }) {
    commit('MOVE_ITEM', { index, oldIndex })
  },
  select({ commit }, { element }) {
    commit('SELECT_ITEM', { element })
  },
  async create({ dispatch }, { pageId, elementType, beforeId = null }) {
    const { data: element } = await ElementService(this.$client).create(
      pageId,
      elementType,
      beforeId
    )

    await dispatch('forceCreate', { element, beforeId })
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
  async fetch({ dispatch, commit }, { page }) {
    commit('CLEAR_ITEMS')

    const { data: elements } = await ElementService(this.$client).fetchAll(
      page.id
    )

    await Promise.all(
      elements.map((element) => dispatch('forceCreate', { element }))
    )

    return elements
  },
  async move({ getters, dispatch }, { elementId, pageId, beforeElementId }) {
    const originalOrder = getters.getElements.map((element) => element.id)
    const newOrder = [...originalOrder]
    const elementIndex = newOrder.findIndex((id) => id === elementId)
    const indexToSwapWith = newOrder.findIndex((id) => id === beforeElementId)

    // The element could be the last or the first one which we need to handle
    if (indexToSwapWith === -1 || indexToSwapWith === newOrder.length) {
      return
    }

    newOrder[elementIndex] = newOrder[indexToSwapWith]
    newOrder[indexToSwapWith] = elementId

    await dispatch('forceMove', {
      index: indexToSwapWith,
      oldIndex: elementIndex,
    })

    try {
      await ElementService(this.$client).order(pageId, newOrder)
    } catch (error) {
      await dispatch('forceMove', {
        index: elementIndex,
        oldIndex: indexToSwapWith,
      })
      throw error
    }
  },
  async duplicate({ getters, dispatch }, { elementId, pageId }) {
    const element = getters.getElements.find((e) => e.id === elementId)
    await dispatch('create', {
      pageId,
      elementType: element.type,
      beforeId: element.id,
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

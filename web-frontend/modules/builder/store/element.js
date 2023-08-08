import ElementService from '@baserow/modules/builder/services/element'
import PublicBuilderService from '@baserow/modules/builder/services/publishedBuilder'
import { calculateTempOrder } from '@baserow/modules/core/utils/order'
import BigNumber from 'bignumber.js'

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
    if (state.selected?.id === elementToUpdate.id) {
      Object.assign(state.selected, values)
    }
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
  forceMove(
    { commit, getters },
    { elementId, beforeElementId, parentElementId, placeInContainer }
  ) {
    const beforeElement = getters.getElementById(beforeElementId)
    const afterOrder = beforeElement?.order || null
    const beforeOrder =
      getters.getPreviousElement(
        beforeElement,
        parentElementId,
        placeInContainer
      )?.order || null
    const tempOrder = calculateTempOrder(beforeOrder, afterOrder)

    commit('UPDATE_ITEM', {
      element: getters.getElementById(elementId),
      values: {
        order: tempOrder,
        parent_element_id: parentElementId,
        place_in_container: placeInContainer,
      },
    })
  },
  select({ commit }, { element }) {
    updateContext.lastUpdatedValues = null
    commit('SELECT_ITEM', { element })
  },
  async create(
    { dispatch },
    {
      pageId,
      elementType,
      beforeId = null,
      configuration = null,
      forceCreate = true,
    }
  ) {
    const { data: element } = await ElementService(this.$client).create(
      pageId,
      elementType,
      beforeId,
      configuration
    )

    if (forceCreate) {
      await dispatch('forceCreate', { element, beforeId })
      await dispatch('select', { element })
    }

    return element
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
  async fetchPublic({ dispatch, commit }, { page }) {
    commit('CLEAR_ITEMS')

    const { data: elements } = await PublicBuilderService(
      this.$client
    ).fetchPublicBuilderElements(page)

    await Promise.all(
      elements.map((element) => dispatch('forceCreate', { element }))
    )

    return elements
  },
  async move(
    { dispatch, getters },
    {
      elementId,
      beforeElementId,
      parentElementId = null,
      placeInContainer = null,
    }
  ) {
    const element = getters.getElementById(elementId)

    await dispatch('forceMove', {
      elementId,
      beforeElementId,
      parentElementId,
      placeInContainer,
    })

    try {
      const { data: elementUpdated } = await ElementService(this.$client).move(
        elementId,
        beforeElementId,
        parentElementId,
        placeInContainer
      )

      dispatch('forceUpdate', {
        element: elementUpdated,
        values: { ...elementUpdated },
      })
    } catch (error) {
      await dispatch('forceUpdate', {
        element,
        values: element,
      })
      throw error
    }
  },
  async duplicate(
    { getters, dispatch },
    { elementId, pageId, configuration = {} }
  ) {
    // TODO this duplication only works with one layer of children
    const element = getters.getElements.find((e) => e.id === elementId)
    const children = getters.getChildren(element)
    const parentCreated = await dispatch('create', {
      pageId,
      beforeId: element.id,
      elementType: element.type,
      configuration: { ...element, ...configuration },
      forceCreate: false,
    })

    const childrenCreated = await Promise.all(
      children.map((child) =>
        dispatch('create', {
          pageId,
          elementType: child.type,
          configuration: {
            ...child,
            parent_element_id: parentCreated.id,
          },
          forceCreate: false,
        })
      )
    )

    await Promise.all(
      childrenCreated.map((child) =>
        dispatch('forceCreate', {
          element: child,
        })
      )
    )

    // We insert the parent element at the end such that the children already exist
    // in the frontend and won't just pop in one after the other
    await dispatch('forceCreate', {
      element: parentCreated,
      beforeId: element.id,
    })

    return [parentCreated, ...childrenCreated]
  },
}

const getters = {
  getElementById: (state, getters) => (id) => {
    return getters.getElements.find((e) => e.id === id)
  },
  getElements: (state) => {
    return state.elements.map((element) => ({
      ...element,
      order: new BigNumber(element.order),
    }))
  },
  getElementsOrdered: (state, getters) => {
    return [...getters.getElements].sort((a, b) => {
      if (a.parent_element_id !== b.parent_element_id) {
        return a.parent_element_id > b.parent_element_id ? 1 : -1
      }
      if (a.place_in_container !== b.place_in_container) {
        return a.place_in_container > b.place_in_container ? 1 : -1
      }
      return a.order.gt(b.order) ? 1 : -1
    })
  },
  getRootElements: (state, getters) => {
    return getters.getElementsOrdered.filter(
      (e) => e.parent_element_id === null
    )
  },
  getChildren: (state, getters) => (element) => {
    return getters.getElementsOrdered.filter(
      (e) => e.parent_element_id === element.id
    )
  },
  getSiblings: (state, getters) => (element) => {
    return getters.getElementsOrdered.filter(
      (e) => e.parent_element_id === element.parent_element_id
    )
  },
  getElementsInPlace: (state, getters) => (parentId, placeInContainer) => {
    return getters.getElementsOrdered.filter(
      (e) =>
        e.parent_element_id === parentId &&
        e.place_in_container === placeInContainer
    )
  },
  getPreviousElement:
    (state, getters) => (before, parentId, placeInContainer) => {
      const elementsInPlace = getters.getElementsInPlace(
        parentId,
        placeInContainer
      )
      return before
        ? elementsInPlace.reverse().find((e) => e.order.lt(before.order)) ||
            null
        : elementsInPlace.at(-1)
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

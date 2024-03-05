import ElementService from '@baserow/modules/builder/services/element'
import PublicBuilderService from '@baserow/modules/builder/services/publishedBuilder'
import { calculateTempOrder } from '@baserow/modules/core/utils/order'
import BigNumber from 'bignumber.js'

const populateElement = (element) => {
  element._ = {
    contentLoading: false,
    content: [],
    hasNextPage: false,
    reset: 0,
    shouldBeFocused: false,
  }

  return element
}

const state = {
  // The currently selected element
  selected: null,
}

const updateContext = {
  updateTimeout: null,
  promiseResolve: null,
  lastUpdatedValues: null,
  valuesToUpdate: {},
}

const mutations = {
  SET_ITEMS(state, { page, elements }) {
    state.selected = null
    page.elements = elements.map(populateElement)
  },
  ADD_ITEM(state, { page, element, beforeId = null }) {
    page.elements.push(populateElement(element))
  },
  UPDATE_ITEM(state, { page, element: elementToUpdate, values }) {
    page.elements.forEach((element) => {
      if (element.id === elementToUpdate.id) {
        Object.assign(element, values)
      }
    })
    if (state.selected?.id === elementToUpdate.id) {
      Object.assign(state.selected, values)
    }
  },
  DELETE_ITEM(state, { page, elementId }) {
    const index = page.elements.findIndex((element) => element.id === elementId)
    if (index > -1) {
      page.elements.splice(index, 1)
    }
  },
  MOVE_ITEM(state, { page, index, oldIndex }) {
    page.elements.splice(index, 0, page.elements.splice(oldIndex, 1)[0])
  },
  SELECT_ITEM(state, { element }) {
    state.selected = element
  },
  CLEAR_ITEMS(state, { page }) {
    page.elements = []
  },
}

const actions = {
  clearAll({ commit }, { page }) {
    commit('CLEAR_ITEMS', { page })
  },
  forceCreate({ commit }, { page, element }) {
    commit('ADD_ITEM', { page, element })

    const elementType = this.$registry.get('element', element.type)
    elementType.afterCreate(element, page)
  },
  forceUpdate({ commit }, { page, element, values }) {
    commit('UPDATE_ITEM', { page, element, values })
    const elementType = this.$registry.get('element', element.type)
    elementType.afterUpdate(element, page)
  },
  forceDelete({ commit, getters }, { page, elementId }) {
    const elementsOfPage = getters.getElements(page)
    const elementIndex = elementsOfPage.findIndex(
      (element) => element.id === elementId
    )
    const elementToDelete = elementsOfPage[elementIndex]

    if (getters.getSelected?.id === elementId) {
      commit('SELECT_ITEM', { element: null })
    }
    commit('DELETE_ITEM', { page, elementId })

    const elementType = this.$registry.get('element', elementToDelete.type)
    elementType.afterDelete(elementToDelete, page)
  },
  forceMove(
    { commit, getters },
    { page, elementId, beforeElementId, parentElementId, placeInContainer }
  ) {
    const beforeElement = getters.getElementById(page, beforeElementId)
    const afterOrder = beforeElement?.order || null
    const beforeOrder =
      getters.getPreviousElement(
        page,
        beforeElement,
        parentElementId,
        placeInContainer
      )?.order || null
    const tempOrder = calculateTempOrder(beforeOrder, afterOrder)

    commit('UPDATE_ITEM', {
      page,
      element: getters.getElementById(page, elementId),
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
      page,
      elementType: elementTypeName,
      beforeId = null,
      configuration = null,
      forceCreate = true,
    }
  ) {
    const elementType = this.$registry.get('element', elementTypeName)
    const { data: element } = await ElementService(this.$client).create(
      page.id,
      elementTypeName,
      beforeId,
      elementType.getDefaultValues(page, configuration)
    )

    if (forceCreate) {
      await dispatch('forceCreate', { page, element })
      await dispatch('select', { element })
    }

    return element
  },
  async update({ dispatch }, { page, element, values }) {
    const oldValues = {}
    const newValues = {}
    Object.keys(values).forEach((name) => {
      if (Object.prototype.hasOwnProperty.call(element, name)) {
        oldValues[name] = element[name]
        newValues[name] = values[name]
      }
    })

    await dispatch('forceUpdate', { page, element, values: newValues })

    try {
      await ElementService(this.$client).update(element.id, values)
    } catch (error) {
      await dispatch('forceUpdate', { page, element, values: oldValues })
      throw error
    }
  },

  async debouncedUpdateSelected({ dispatch, getters }, { page, values }) {
    const element = getters.getSelected

    const oldValues = {}
    Object.keys(values).forEach((name) => {
      if (Object.prototype.hasOwnProperty.call(element, name)) {
        oldValues[name] = element[name]
        // Accumulate the changed values to send all the ongoing changes with the
        // final request
        updateContext.valuesToUpdate[name] = values[name]
      }
    })

    await dispatch('forceUpdate', {
      page,
      element,
      values: updateContext.valuesToUpdate,
    })

    return new Promise((resolve, reject) => {
      const fire = async () => {
        const toUpdate = updateContext.valuesToUpdate
        updateContext.valuesToUpdate = {}
        try {
          await ElementService(this.$client).update(element.id, toUpdate)
          updateContext.lastUpdatedValues = null
          resolve()
        } catch (error) {
          // Revert to old values on error
          await dispatch('forceUpdate', {
            page,
            element,
            values: updateContext.lastUpdatedValues,
          })
          updateContext.lastUpdatedValues = null
          reject(error)
        }
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
  async delete({ dispatch, getters }, { page, elementId }) {
    const elementsOfPage = getters.getElements(page)
    const elementIndex = elementsOfPage.findIndex(
      (element) => element.id === elementId
    )
    const elementToDelete = elementsOfPage[elementIndex]

    const descendants = getters.getDescendants(page, elementToDelete)

    // First delete all children
    await Promise.all(
      descendants.map((descendant) =>
        dispatch('forceDelete', { page, elementId: descendant.id })
      )
    )

    await dispatch('forceDelete', { page, elementId })

    try {
      await ElementService(this.$client).delete(elementId)
    } catch (error) {
      await dispatch('forceCreate', {
        page,
        element: elementToDelete,
      })
      // Then restore all children
      await Promise.all(
        descendants.map((descendant) =>
          dispatch('forceCreate', { page, element: descendant })
        )
      )
      throw error
    }
  },
  async fetch({ commit }, { page }) {
    const { data: elements } = await ElementService(this.$client).fetchAll(
      page.id
    )

    commit('SET_ITEMS', { page, elements })

    return elements
  },
  async fetchPublished({ commit }, { page }) {
    const { data: elements } = await PublicBuilderService(
      this.$client
    ).fetchElements(page)

    commit('SET_ITEMS', { page, elements })

    return elements
  },
  async move(
    { commit, dispatch, getters },
    {
      page,
      elementId,
      beforeElementId,
      parentElementId = null,
      placeInContainer = null,
    }
  ) {
    const element = getters.getElementById(page, elementId)

    await dispatch('forceMove', {
      page,
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
        page,
        element: elementUpdated,
        values: { ...elementUpdated },
      })
    } catch (error) {
      await dispatch('forceUpdate', {
        page,
        element,
        values: element,
      })
      throw error
    }
  },
  async duplicate({ commit, dispatch, getters }, { page, elementId }) {
    const {
      data: { elements, workflow_actions: workflowActions },
    } = await ElementService(this.$client).duplicate(elementId)

    const elementPromises = elements.map((element) =>
      dispatch('forceCreate', { page, element })
    )
    const workflowActionPromises = workflowActions.map((workflowAction) =>
      dispatch(
        'workflowAction/forceCreate',
        { page, workflowAction },
        { root: true }
      )
    )

    await Promise.all(elementPromises.concat(workflowActionPromises))

    const elementToDuplicate = getters.getElementById(page, elementId)
    const elementToSelect = elements.find(
      ({ parent_element_id: parentId }) =>
        parentId === elementToDuplicate.parent_element_id
    )

    commit('SELECT_ITEM', { element: elementToSelect })

    return elements
  },
  emitElementEvent({ getters }, { event, page, ...rest }) {
    const elements = getters.getElements(page)

    elements.forEach((element) => {
      const elementType = this.$registry.get('element', element.type)
      elementType.onElementEvent(event, { page, element, ...rest })
    })
  },
}

/** Recursively order the elements from up to down and left to right */
const orderElements = (elements, parentElementId = null) => {
  return elements
    .filter(
      ({ parent_element_id: curentParentElementId }) =>
        curentParentElementId === parentElementId
    )
    .sort((a, b) => {
      if (a.place_in_container !== b.place_in_container) {
        return a.place_in_container > b.place_in_container ? 1 : -1
      }

      return a.order.gt(b.order) ? 1 : -1
    })
    .map((element) => [element, ...orderElements(elements, element.id)])
    .flat()
}

const getters = {
  getElements: (state) => (page) => {
    return page.elements.map((element) => ({
      ...element,
      order: new BigNumber(element.order),
    }))
  },
  getElementById: (state, getters) => (page, id) => {
    return getters.getElements(page).find((e) => e.id === id)
  },
  getElementsOrdered: (state, getters) => (page) => {
    return orderElements(getters.getElements(page))
  },
  getRootElements: (state, getters) => (page) => {
    return getters
      .getElementsOrdered(page)
      .filter((e) => e.parent_element_id === null)
  },
  getChildren: (state, getters) => (page, element) => {
    return getters
      .getElementsOrdered(page)
      .filter((e) => e.parent_element_id === element.id)
  },
  getDescendants: (state, getters) => (page, element) => {
    return getters
      .getChildren(page, element)
      .map((child) => [...getters.getChildren(page, child), child])
      .flat()
  },
  getAncestors: (state, getters) => (page, element) => {
    const getElementAncestors = (element) => {
      if (element.parent_element_id === null) {
        return []
      } else {
        const parentElement = getters.getElementById(
          page,
          element.parent_element_id
        )
        return [...getElementAncestors(parentElement), parentElement]
      }
    }
    return getElementAncestors(element)
  },
  getSiblings: (state, getters) => (page, element) => {
    return getters
      .getElementsOrdered(page)
      .filter((e) => e.parent_element_id === element.parent_element_id)
  },
  getElementPosition:
    (state, getters) =>
    (page, element, sameType = false) => {
      const elements = getters.getElementsOrdered(page)

      return (
        (sameType
          ? elements.filter(({ type }) => type === element.type)
          : elements
        ).findIndex(({ id }) => id === element.id) + 1
      )
    },
  getElementsInPlace:
    (state, getters) => (page, parentId, placeInContainer) => {
      return getters
        .getElementsOrdered(page)
        .filter(
          (e) =>
            e.parent_element_id === parentId &&
            e.place_in_container === placeInContainer
        )
    },
  getPreviousElement:
    (state, getters) => (page, before, parentId, placeInContainer) => {
      const elementsInPlace = getters.getElementsInPlace(
        page,
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

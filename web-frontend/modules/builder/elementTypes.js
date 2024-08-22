import { Registerable } from '@baserow/modules/core/registry'
import TextElement from '@baserow/modules/builder/components/elements/components/TextElement'
import HeadingElement from '@baserow/modules/builder/components/elements/components/HeadingElement'
import LinkElement from '@baserow/modules/builder/components/elements/components/LinkElement'
import TextElementForm from '@baserow/modules/builder/components/elements/components/forms/general/TextElementForm'
import HeadingElementForm from '@baserow/modules/builder/components/elements/components/forms/general/HeadingElementForm'
import LinkElementForm from '@baserow/modules/builder/components/elements/components/forms/general/LinkElementForm'
import ImageElementForm from '@baserow/modules/builder/components/elements/components/forms/general/ImageElementForm'
import ImageElement from '@baserow/modules/builder/components/elements/components/ImageElement'
import InputTextElement from '@baserow/modules/builder/components/elements/components/InputTextElement'
import InputTextElementForm from '@baserow/modules/builder/components/elements/components/forms/general/InputTextElementForm'
import TableElement from '@baserow/modules/builder/components/elements/components/TableElement'
import TableElementForm from '@baserow/modules/builder/components/elements/components/forms/general/TableElementForm'
import {
  ensureArray,
  ensureBoolean,
  ensureString,
} from '@baserow/modules/core/utils/validator'
import {
  CHOICE_OPTION_TYPES,
  ELEMENT_EVENTS,
  PLACEMENTS,
} from '@baserow/modules/builder/enums'
import ColumnElement from '@baserow/modules/builder/components/elements/components/ColumnElement'
import ColumnElementForm from '@baserow/modules/builder/components/elements/components/forms/general/ColumnElementForm'
import _ from 'lodash'
import DefaultStyleForm from '@baserow/modules/builder/components/elements/components/forms/style/DefaultStyleForm'
import ButtonElement from '@baserow/modules/builder/components/elements/components/ButtonElement'
import ButtonElementForm from '@baserow/modules/builder/components/elements/components/forms/general/ButtonElementForm'
import { ClickEvent, SubmitEvent } from '@baserow/modules/builder/eventTypes'
import RuntimeFormulaContext from '@baserow/modules/core/runtimeFormulaContext'
import { resolveFormula } from '@baserow/modules/core/formula'
import FormContainerElement from '@baserow/modules/builder/components/elements/components/FormContainerElement.vue'
import FormContainerElementForm from '@baserow/modules/builder/components/elements/components/forms/general/FormContainerElementForm.vue'
import ChoiceElement from '@baserow/modules/builder/components/elements/components/ChoiceElement.vue'
import ChoiceElementForm from '@baserow/modules/builder/components/elements/components/forms/general/ChoiceElementForm.vue'
import CheckboxElement from '@baserow/modules/builder/components/elements/components/CheckboxElement.vue'
import CheckboxElementForm from '@baserow/modules/builder/components/elements/components/forms/general/CheckboxElementForm.vue'
import IFrameElement from '@baserow/modules/builder/components/elements/components/IFrameElement.vue'
import IFrameElementForm from '@baserow/modules/builder/components/elements/components/forms/general/IFrameElementForm.vue'
import RepeatElement from '@baserow/modules/builder/components/elements/components/RepeatElement'
import RepeatElementForm from '@baserow/modules/builder/components/elements/components/forms/general/RepeatElementForm'
import { pathParametersInError } from '@baserow/modules/builder/utils/params'
import { isNumeric, isValidEmail } from '@baserow/modules/core/utils/string'

export class ElementType extends Registerable {
  get name() {
    return null
  }

  get description() {
    return null
  }

  get iconClass() {
    return null
  }

  get component() {
    return null
  }

  get editComponent() {
    return this.component
  }

  get generalFormComponent() {
    return null
  }

  get styleFormComponent() {
    return DefaultStyleForm
  }

  get stylesAll() {
    return [
      'style_padding_top',
      'style_padding_bottom',
      'style_padding_left',
      'style_padding_right',
      'style_margin_top',
      'style_margin_bottom',
      'style_margin_left',
      'style_margin_right',
      'style_border_top',
      'style_border_bottom',
      'style_border_left',
      'style_border_right',
      'style_background',
      'style_background_color',
      'style_background_file',
      'style_background_mode',
      'style_width',
    ]
  }

  get styles() {
    return this.stylesAll
  }

  /**
   * Returns a display name for this element, so it can be distinguished from
   * other elements of the same type.
   * @param {object} element - The element we want to get a display name for.
   * @param {object} applicationContext - The context of the current application
   * @returns {string} this element's display name.
   */
  getDisplayName(element, applicationContext) {
    return this.name
  }

  getEvents(element) {
    return []
  }

  getEventByName(element, name) {
    return this.getEvents(element).find((event) => event.name === name)
  }

  /**
   * Returns whether the element configuration is valid or not.
   * @param {object} param An object containing the element and the builder
   * @returns true if the element is in error
   */
  isInError({ element, builder }) {
    return false
  }

  /**
   * Allow to hook into default values for this element type at element creation.
   * @param {object} values the current values for the element to create.
   * @returns an object containing values updated with the default values.
   */
  getDefaultValues(page, values) {
    // By default if an element is inside a container we apply the
    // `.getDefaultChildValues()` method of the parent to it.
    if (values?.parent_element_id) {
      const parentElement = this.app.store.getters['element/getElementById'](
        page,
        values.parent_element_id
      )
      const parentElementType = this.app.$registry.get(
        'element',
        parentElement.type
      )
      return {
        ...values,
        ...parentElementType.getDefaultChildValues(page, values),
      }
    }
    return values
  }

  /**
   * When a data source is modified or destroyed, `element/emitElementEvent`
   * can be dispatched to notify all elements of the event. Element types
   * can implement this function to handle the cases.
   *
   * @param event - `ELEMENT_EVENTS.DATA_SOURCE_REMOVED` if a data source
   *  has been destroyed, or `ELEMENT_EVENTS.DATA_SOURCE_AFTER_UPDATE` if
   *  it's been updated.
   * @param params - Context data which the element type can use.
   */
  onElementEvent(event, params) {}

  resolveFormula(formula, applicationContext) {
    const formulaFunctions = {
      get: (name) => {
        return this.app.$registry.get('runtimeFormulaFunction', name)
      },
    }

    const runtimeFormulaContext = new Proxy(
      new RuntimeFormulaContext(
        this.app.$registry.getAll('builderDataProvider'),
        applicationContext
      ),
      {
        get(target, prop) {
          return target.get(prop)
        },
      }
    )

    return resolveFormula(formula, formulaFunctions, runtimeFormulaContext)
  }

  /**
   * Responsible for returning an array of collection element IDs that represent
   * the ancestry of this element. It's used to determine the accessible path
   * between elements that have access to the form data provider. If an element
   * is in the path of a form element, then it can use its form data.
   *
   * @param {Object} element - The element we're the path for.
   * @param {Object} page - The page the element belongs to.
   */
  getElementNamespacePath(element, page) {
    const ancestors = this.app.store.getters['element/getAncestors'](
      page,
      element
    )
    return ancestors
      .map((ancestor) => {
        const elementType = this.app.$registry.get('element', ancestor.type)
        return elementType.isCollectionElement ? ancestor.id : null
      })
      .filter((id) => id !== null)
      .reverse()
  }

  /**
   * A hook that is triggered right after an element is created.
   *
   * @param element - The element that was just created
   * @param page - The page the element belongs to
   */
  afterCreate(element, page) {}

  /**
   * A hook that is triggered right after an element is deleted.
   *
   * @param element - The element that was just deleted
   * @param page - The page the element belongs to
   */
  afterDelete(element, page) {}

  /**
   * A hook that is trigger right after an element has been updated.
   * @param element - The updated element
   * @param page - The page the element belong to
   */
  afterUpdate(element, page) {}

  /**
   * Move a component in the same place.
   * @param {Object} page - The page the element belongs to
   * @param {Object} element - The element to move
   * @param {String} placement - The direction of the move
   */
  async moveElementInSamePlace(page, element, placement) {
    let beforeElementId = null

    switch (placement) {
      case PLACEMENTS.BEFORE: {
        const previousElement = this.app.store.getters[
          'element/getPreviousElement'
        ](page, element)

        beforeElementId = previousElement ? previousElement.id : null
        break
      }
      case PLACEMENTS.AFTER: {
        const nextElement = this.app.store.getters['element/getNextElement'](
          page,
          element
        )

        if (nextElement) {
          const nextNextElement = this.app.store.getters[
            'element/getNextElement'
          ](page, nextElement)
          beforeElementId = nextNextElement ? nextNextElement.id : null
        }
        break
      }
    }

    await this.app.store.dispatch('element/move', {
      page,
      elementId: element.id,
      beforeElementId,
      parentElementId: element.parent_element_id
        ? element.parent_element_id
        : null,
      placeInContainer: element.place_in_container,
    })
  }

  /**
   * Move an element according to the new placement.
   * @param {Object} page - The page the element belongs to
   * @param {Object} element - The element to move
   * @param {String} placement - The direction of the move
   */
  async moveElement(page, element, placement) {
    if (element.parent_element_id !== null) {
      const parentElement = this.app.store.getters['element/getElementById'](
        page,
        element.parent_element_id
      )

      const parentElementType = this.app.$registry.get(
        'element',
        parentElement.type
      )
      await parentElementType.moveChildElement(
        page,
        parentElement,
        element,
        placement
      )
    } else {
      await this.moveElementInSamePlace(page, element, placement)
    }
  }

  /**
   * Identify and select the next element according to the new placement.
   *
   * @param {Object} page - The page the element belongs to
   * @param {Object} element - The element on which the selection should be based on
   * @param {String} placement - The direction of the selection
   */
  async selectNextElement(page, element, placement) {
    let elementToBeSelected = null
    if (placement === PLACEMENTS.BEFORE) {
      elementToBeSelected = this.app.store.getters[
        'element/getPreviousElement'
      ](page, element)
    } else if (placement === PLACEMENTS.AFTER) {
      elementToBeSelected = this.app.store.getters['element/getNextElement'](
        page,
        element
      )
    } else {
      const containerElement = this.app.store.getters['element/getElementById'](
        page,
        element.parent_element_id
      )
      const containerElementType = this.app.$registry.get(
        'element',
        containerElement.type
      )
      elementToBeSelected =
        containerElementType.getNextHorizontalElementToSelect(
          page,
          element,
          placement
        )
    }

    if (!elementToBeSelected) {
      return
    }

    try {
      await this.app.store.dispatch('element/select', {
        element: elementToBeSelected,
      })
    } catch {}
  }

  /**
   * Returns vertical placement disabled.
   * @param {Object} page - The page the element belongs to
   * @param {Object} element - The element to move
   * @param {String} placement - The direction of the move
   */
  getVerticalPlacementsDisabled(page, element) {
    const previousElement = this.app.store.getters[
      'element/getPreviousElement'
    ](page, element)
    const nextElement = this.app.store.getters['element/getNextElement'](
      page,
      element
    )

    const placementsDisabled = []

    if (!previousElement) {
      placementsDisabled.push(PLACEMENTS.BEFORE)
    }

    if (!nextElement) {
      placementsDisabled.push(PLACEMENTS.AFTER)
    }

    return placementsDisabled
  }

  /**
   * Return an array of placements that are disallowed for the element to move
   * in their container (or root page).
   *
   * @param {Object} page The page that is the parent component.
   * @param {Number} element The element for which the placements should be
   *  calculated.
   * @returns {Array} An array of placements that are disallowed for the element.
   */
  getPlacementsDisabled(page, element) {
    // If the element has a parent, let the parent container type derive the
    // disabled placements.
    if (element.parent_element_id) {
      const containerElement = this.app.store.getters['element/getElementById'](
        page,
        element.parent_element_id
      )
      const elementType = this.app.$registry.get(
        'element',
        containerElement.type
      )
      return elementType.getPlacementsDisabledForChild(
        page,
        containerElement,
        element
      )
    }

    return [
      PLACEMENTS.LEFT,
      PLACEMENTS.RIGHT,
      ...this.getVerticalPlacementsDisabled(page, element),
    ]
  }

  /**
   * Generates a unique element id based on the element and if provided, an array
   * representing a path to access form data. Most elements will have a unique
   * ID that matches their `id`, but when an element is part of one or more repeats,
   * we need to ensure that the ID is unique for each record.
   *
   * @param {Object} element - The element we want to generate a unique ID for.
   * @param {Array} recordIndexPath - An array of integers which represent the
   * record indices we've accumulated through nested collection element ancestors.
   * @returns {String} - The unique element ID.
   *
   */
  uniqueElementId(element, recordIndexPath) {
    return [element.id, ...(recordIndexPath || [])].join('.')
  }

  /**
   * Responsible for optionally extending the element store's
   * `_` object with per-element type specific properties.
   * @returns {Object} - An object containing the properties to be added.
   */
  getPopulateStoreProperties() {
    return {}
  }
}

const ContainerElementTypeMixin = (Base) =>
  class extends Base {
    isContainerElement = true

    get elementTypesAll() {
      return Object.values(this.app.$registry.getAll('element'))
    }

    /**
     * Returns an array of element types that are not allowed as children of this element type.
     * @returns {Array} An array of forbidden child element types.
     */
    get childElementTypesForbidden() {
      return []
    }

    /**
     * Returns an array of element types that are allowed as children of this element.
     * If the parent element we're trying to add a child to has a parent, we'll check
     * each parent until the root element if they have any forbidden element types to
     * include as well.
     * @param page
     * @param element
     * @returns {Array} An array of permitted child element types.
     */
    childElementTypes(page, element) {
      if (element.parent_element_id) {
        const parentElement = this.app.store.getters['element/getElementById'](
          page,
          element.parent_element_id
        )
        const parentElementType = this.app.$registry.get(
          'element',
          parentElement.type
        )
        return _.difference(
          parentElementType.childElementTypes(page, parentElement),
          this.childElementTypesForbidden
        )
      }
      return _.difference(this.elementTypesAll, this.childElementTypesForbidden)
    }

    /**
     * Returns an array of style types that are not allowed as children of this element.
     * @returns {Array}
     */
    get childStylesForbidden() {
      return []
    }

    get defaultPlaceInContainer() {
      throw new Error('Not implemented')
    }

    /**
     * Returns the default value when creating a child element to this container.
     * @param {Object} page The current page object
     * @param {Object} values The values of the to be created element
     * @returns the default values for this element.
     */
    getDefaultChildValues(page, values) {
      // By default, an element inside a container should have no left and right padding
      return { style_padding_left: 0, style_padding_right: 0 }
    }

    /**
     * Given a `page` and an `element`, move the child element of a container
     * in the direction specified by the `placement`.
     *
     * The default implementation only supports moving the element vertically.
     *
     * @param {Object} page The page that is the parent component.
     * @param {Number} element The child element to be moved.
     * @param {String} placement The direction in which the element should move.
     */
    async moveChildElement(page, parentElement, element, placement) {
      if (placement === PLACEMENTS.AFTER || placement === PLACEMENTS.BEFORE) {
        await this.moveElementInSamePlace(page, element, placement)
      }
    }

    /**
     * Return an array of placements that are disallowed for the elements to move
     * in their container.
     *
     * @param {Object} page The page that is the parent component.
     * @param {Number} element The child element for which the placements should
     *    be calculated.
     * @returns {Array} An array of placements that are disallowed for the element.
     */
    getPlacementsDisabledForChild(page, containerElement, element) {
      this.getPlacementsDisabled(page, element)
    }

    getNextHorizontalElementToSelect(page, element, placement) {
      return null
    }
  }

export class FormContainerElementType extends ContainerElementTypeMixin(
  ElementType
) {
  static getType() {
    return 'form_container'
  }

  get name() {
    return this.app.i18n.t('elementType.formContainer')
  }

  get description() {
    return this.app.i18n.t('elementType.formContainerDescription')
  }

  get iconClass() {
    return 'iconoir-frame'
  }

  get component() {
    return FormContainerElement
  }

  get generalFormComponent() {
    return FormContainerElementForm
  }

  /**
   * Exclude element types which are not a form element.
   * @returns {Array} An array of non-form element types.
   */
  get childElementTypesForbidden() {
    return this.elementTypesAll.filter((type) => !type.isFormElement)
  }

  get childStylesForbidden() {
    return ['style_width']
  }

  getEvents(element) {
    return [new SubmitEvent({ ...this.app })]
  }

  /**
   * Return an array of placements that are disallowed for the elements to move
   * in their container.
   *
   * @param {Object} page The page that is the parent component.
   * @param {Number} element The child element for which the placements should
   *    be calculated.
   * @returns {Array} An array of placements that are disallowed for the element.
   */
  getPlacementsDisabledForChild(page, containerElement, element) {
    return [
      PLACEMENTS.LEFT,
      PLACEMENTS.RIGHT,
      ...this.getVerticalPlacementsDisabled(page, element),
    ]
  }
}

export class ColumnElementType extends ContainerElementTypeMixin(ElementType) {
  static getType() {
    return 'column'
  }

  get name() {
    return this.app.i18n.t('elementType.column')
  }

  get description() {
    return this.app.i18n.t('elementType.columnDescription')
  }

  get iconClass() {
    return 'iconoir-view-columns-3'
  }

  get component() {
    return ColumnElement
  }

  get generalFormComponent() {
    return ColumnElementForm
  }

  /**
   * Exclude element types which are containers.
   * @returns {Array} An array of container element types.
   */
  get childElementTypesForbidden() {
    return this.elementTypesAll.filter(
      (elementType) => elementType.isContainerElement
    )
  }

  get childStylesForbidden() {
    return ['style_width']
  }

  get defaultPlaceInContainer() {
    return '0'
  }

  /**
   * Given a `page` and an `element`, move the child element of a container
   * in the direction specified by the `placement`.
   *
   * @param {Object} page The page that is the parent component.
   * @param {Number} element The child element to be moved.
   * @param {String} placement The direction in which the element should move.
   */
  async moveChildElement(page, parentElement, element, placement) {
    if (placement === PLACEMENTS.AFTER || placement === PLACEMENTS.BEFORE) {
      await super.moveChildElement(page, parentElement, element, placement)
    } else {
      const placeInContainer = parseInt(element.place_in_container)
      const newPlaceInContainer =
        placement === PLACEMENTS.LEFT
          ? placeInContainer - 1
          : placeInContainer + 1

      if (newPlaceInContainer >= 0) {
        await this.app.store.dispatch('element/move', {
          page,
          elementId: element.id,
          beforeElementId: null,
          parentElementId: parentElement.id,
          placeInContainer: `${newPlaceInContainer}`,
        })
      }
    }
  }

  /**
   * Return an array of placements that are disallowed for the elements to move
   * in their container.
   *
   * @param {Object} page The page that is the parent component.
   * @param {Number} element The child element for which the placements should
   *    be calculated.
   * @returns {Array} An array of placements that are disallowed for the element.
   */
  getPlacementsDisabledForChild(page, containerElement, element) {
    const columnIndex = parseInt(element.place_in_container)

    const placementsDisabled = []

    if (columnIndex === 0) {
      placementsDisabled.push(PLACEMENTS.LEFT)
    }

    if (columnIndex === containerElement.column_amount - 1) {
      placementsDisabled.push(PLACEMENTS.RIGHT)
    }

    return [
      ...placementsDisabled,
      ...this.getVerticalPlacementsDisabled(page, element),
    ]
  }

  getNextHorizontalElementToSelect(page, element, placement) {
    const offset = placement === PLACEMENTS.LEFT ? -1 : 1
    const containerElement = this.app.store.getters['element/getElementById'](
      page,
      element.parent_element_id
    )

    let elementsInPlace = []
    let nextPlaceInContainer = parseInt(element.place_in_container)
    for (let i = 0; i < containerElement.column_amount; i++) {
      nextPlaceInContainer += offset
      elementsInPlace = this.app.store.getters['element/getElementsInPlace'](
        page,
        containerElement.id,
        nextPlaceInContainer.toString()
      )

      if (elementsInPlace.length) {
        return elementsInPlace[elementsInPlace.length - 1]
      }
    }

    return null
  }
}

const CollectionElementTypeMixin = (Base) =>
  class extends Base {
    isCollectionElement = true
    getDisplayName(element, { page }) {
      let suffix = ''

      if (element.data_source_id) {
        const dataSource = this.app.store.getters[
          'dataSource/getPageDataSourceById'
        ](page, element.data_source_id)

        suffix = dataSource ? ` - ${dataSource.name}` : ''
      }

      return `${this.name}${suffix}`
    }

    /**
     * When a data source is modified or destroyed, we need to ensure that
     * our collection elements respond accordingly.
     *
     * If the data source has been removed, we want to remove it from the
     * collection element, and then clear its contents from the store.
     *
     * If the data source has been updated, we want to trigger a content reset.
     *
     * @param event - `ELEMENT_EVENTS.DATA_SOURCE_REMOVED` if a data source
     *  has been destroyed, or `ELEMENT_EVENTS.DATA_SOURCE_AFTER_UPDATE` if
     *  it's been updated.
     * @param params - Context data which the element type can use.
     */
    async onElementEvent(event, { page, element, dataSourceId }) {
      if (event === ELEMENT_EVENTS.DATA_SOURCE_REMOVED) {
        if (element.data_source_id === dataSourceId) {
          // Remove the data_source_id
          await this.app.store.dispatch('element/forceUpdate', {
            page,
            element,
            values: { data_source_id: null },
          })
          // Empty the element content
          await this.app.store.dispatch('elementContent/clearElementContent', {
            element,
          })
        }
      }
      if (event === ELEMENT_EVENTS.DATA_SOURCE_AFTER_UPDATE) {
        if (element.data_source_id === dataSourceId) {
          await this.app.store.dispatch(
            'elementContent/triggerElementContentReset',
            {
              element,
            }
          )
        }
      }
    }
  }

export class TableElementType extends CollectionElementTypeMixin(ElementType) {
  static getType() {
    return 'table'
  }

  get name() {
    return this.app.i18n.t('elementType.table')
  }

  get description() {
    return this.app.i18n.t('elementType.tableDescription')
  }

  get iconClass() {
    return 'iconoir-table'
  }

  get component() {
    return TableElement
  }

  get generalFormComponent() {
    return TableElementForm
  }

  getEvents(element) {
    return (element.fields || [])
      .map((field) => {
        const { type, name, uid } = field
        const collectionFieldType = this.app.$registry.get(
          'collectionField',
          type
        )
        return collectionFieldType.events.map((EventType) => {
          return new EventType({
            ...this.app,
            namePrefix: uid,
            labelSuffix: `- ${name}`,
            applicationContextAdditions: { collectionField: field },
          })
        })
      })
      .flat()
  }

  isInError({ element, builder }) {
    const collectionFieldsInError = element.fields.map((collectionField) => {
      const collectionFieldType = this.app.$registry.get(
        'collectionField',
        collectionField.type
      )
      return collectionFieldType.isInError({
        field: collectionField,
        builder,
      })
    })
    return collectionFieldsInError.includes(true)
  }
}

export class RepeatElementType extends ContainerElementTypeMixin(
  CollectionElementTypeMixin(ElementType)
) {
  static getType() {
    return 'repeat'
  }

  get name() {
    return this.app.i18n.t('elementType.repeat')
  }

  get description() {
    return this.app.i18n.t('elementType.repeatDescription')
  }

  get iconClass() {
    return 'iconoir-repeat'
  }

  get component() {
    return RepeatElement
  }

  get generalFormComponent() {
    return RepeatElementForm
  }

  /**
   * The repeat elements will disallow collection elements (including itself),
   * from being added as children.
   * @returns {Array} An array of disallowed child element types.
   */
  get childElementTypesForbidden() {
    return this.elementTypesAll.filter((type) => type.isCollectionElement)
  }

  /**
   * Return an array of placements that are disallowed for the elements to move
   * in their container.
   *
   * @param {Object} page The page that is the parent component.
   * @param {Number} element The child element for which the placements should
   *    be calculated.
   * @returns {Array} An array of placements that are disallowed for the element.
   */
  getPlacementsDisabledForChild(page, containerElement, element) {
    return [
      PLACEMENTS.LEFT,
      PLACEMENTS.RIGHT,
      ...this.getVerticalPlacementsDisabled(page, element),
    ]
  }

  /**
   * A repeat element is in error whilst it has no data source.
   * @param {Object} element - The repeat element
   * @param {Object} builder - The builder application.
   * @returns {Boolean} - Whether the element is in error.
   */
  isInError({ element, builder }) {
    return element.data_source_id === null
  }

  /**
   * Responsible for extending the element store's `populateElement`
   * `_` object with repeat element specific properties.
   * @returns {Object} - An object containing the properties to be added.
   */
  getPopulateStoreProperties() {
    return { collapsed: false }
  }
}
/**
 * This class serves as a parent class for all form element types. Form element types
 * are all elements that can be used as part of a form. So in simple terms, any element
 * that can represents data in a way that is directly modifiable by an application user.
 */
export class FormElementType extends ElementType {
  isFormElement = true

  formDataType(element) {
    return null
  }

  /**
   * Given a form element, and a form data value, is responsible for validating
   * this form element type against that value. Returns whether the value is valid.
   * @param element - The form element
   * @param value - The value to be validated against
   * @param applicationContext - The context of the current application
   * @returns {boolean}
   */
  isValid(element, value) {
    return !(element.required && !value)
  }

  /**
   * Get the initial form data value of an element.
   * @param element - The form element
   * @param applicationContext - The context of the current application
   * @returns {any} - The initial data that's supposed to be stored
   */
  getInitialFormDataValue(element, applicationContext) {
    throw new Error('.getInitialFormData needs to be implemented')
  }

  /**
   * Returns a display name for this element, so it can be distinguished from
   * other elements of the same type.
   * @param {object} element - The element we want to get a display name for.
   * @param {object} applicationContext
   * @returns {string} this element's display name.
   */
  getDisplayName(element, applicationContext) {
    if (element.label) {
      const resolvedName = ensureString(
        this.resolveFormula(element.label, applicationContext)
      ).trim()
      return resolvedName || this.name
    }
    return this.name
  }

  afterDelete(element, page) {
    return this.app.store.dispatch('formData/removeFormData', {
      page,
      elementId: element.id,
    })
  }

  getNextHorizontalElementToSelect(page, element, placement) {
    return null
  }

  getDataSchema(element) {
    return {
      type: this.formDataType(element),
    }
  }
}

export class InputTextElementType extends FormElementType {
  static getType() {
    return 'input_text'
  }

  isValid(element, value, applicationContext) {
    if (!value) {
      return !element.required
    }

    switch (element.validation_type) {
      case 'integer':
        return isNumeric(value)
      case 'email':
        return isValidEmail(value)
      default:
        return true
    }
  }

  get name() {
    return this.app.i18n.t('elementType.inputText')
  }

  get description() {
    return this.app.i18n.t('elementType.inputTextDescription')
  }

  get iconClass() {
    return 'iconoir-input-field'
  }

  get component() {
    return InputTextElement
  }

  get generalFormComponent() {
    return InputTextElementForm
  }

  formDataType(element) {
    return 'string'
  }

  getDisplayName(element, applicationContext) {
    const displayValue =
      element.label || element.default_value || element.placeholder

    if (displayValue?.trim()) {
      const resolvedName = ensureString(
        this.resolveFormula(displayValue, applicationContext)
      ).trim()
      return resolvedName || this.name
    }
    return this.name
  }

  getInitialFormDataValue(element, applicationContext) {
    try {
      return this.resolveFormula(element.default_value, {
        element,
        ...applicationContext,
      })
    } catch {
      return ''
    }
  }
}

export class HeadingElementType extends ElementType {
  static getType() {
    return 'heading'
  }

  get name() {
    return this.app.i18n.t('elementType.heading')
  }

  get description() {
    return this.app.i18n.t('elementType.headingDescription')
  }

  get iconClass() {
    return 'iconoir-text'
  }

  get component() {
    return HeadingElement
  }

  get generalFormComponent() {
    return HeadingElementForm
  }

  getDisplayName(element, applicationContext) {
    if (element.value && element.value.length) {
      const resolvedName = ensureString(
        this.resolveFormula(element.value, applicationContext)
      ).trim()
      return resolvedName || this.name
    }
    return this.name
  }
}

export class TextElementType extends ElementType {
  static getType() {
    return 'text'
  }

  get name() {
    return this.app.i18n.t('elementType.text')
  }

  get description() {
    return this.app.i18n.t('elementType.textDescription')
  }

  get iconClass() {
    return 'iconoir-text-box'
  }

  get component() {
    return TextElement
  }

  get generalFormComponent() {
    return TextElementForm
  }

  getDisplayName(element, applicationContext) {
    if (element.value) {
      const resolvedName = ensureString(
        this.resolveFormula(element.value, applicationContext)
      ).trim()
      return resolvedName || this.name
    }
    return this.name
  }
}

export class LinkElementType extends ElementType {
  static getType() {
    return 'link'
  }

  get name() {
    return this.app.i18n.t('elementType.link')
  }

  get description() {
    return this.app.i18n.t('elementType.linkDescription')
  }

  get iconClass() {
    return 'iconoir-link'
  }

  get component() {
    return LinkElement
  }

  get generalFormComponent() {
    return LinkElementForm
  }

  isInError({ element, builder }) {
    return pathParametersInError(element, builder)
  }

  getDisplayName(element, applicationContext) {
    let displayValue = ''
    let destination = ''
    if (element.navigation_type === 'page') {
      const builder = applicationContext.builder
      const destinationPage = builder.pages.find(
        ({ id }) => id === element.navigate_to_page_id
      )
      if (destinationPage) {
        destination = `${destinationPage.name}`
      }
    } else if (element.navigation_type === 'custom') {
      destination = ensureString(
        this.resolveFormula(element.navigate_to_url, applicationContext)
      ).trim()
    }

    if (destination) {
      destination = ` -> ${destination}`
    }

    if (element.value) {
      displayValue = ensureString(
        this.resolveFormula(element.value, applicationContext)
      ).trim()
    }

    return displayValue
      ? `${displayValue}${destination}`
      : `${this.name}${destination}`
  }
}

export class ImageElementType extends ElementType {
  static getType() {
    return 'image'
  }

  get name() {
    return this.app.i18n.t('elementType.image')
  }

  get description() {
    return this.app.i18n.t('elementType.imageDescription')
  }

  get iconClass() {
    return 'iconoir-media-image'
  }

  get component() {
    return ImageElement
  }

  get generalFormComponent() {
    return ImageElementForm
  }

  getDisplayName(element, applicationContext) {
    if (element.alt_text) {
      const resolvedName = ensureString(
        this.resolveFormula(element.alt_text, applicationContext)
      ).trim()
      return resolvedName || this.name
    }
    return this.name
  }
}

export class ButtonElementType extends ElementType {
  static getType() {
    return 'button'
  }

  get name() {
    return this.app.i18n.t('elementType.button')
  }

  get description() {
    return this.app.i18n.t('elementType.buttonDescription')
  }

  get iconClass() {
    return 'iconoir-square-cursor'
  }

  get component() {
    return ButtonElement
  }

  get generalFormComponent() {
    return ButtonElementForm
  }

  getEvents(element) {
    return [new ClickEvent({ ...this.app })]
  }

  getDisplayName(element, applicationContext) {
    if (element.value) {
      const resolvedName = ensureString(
        this.resolveFormula(element.value, applicationContext)
      ).trim()
      return resolvedName || this.name
    }
    return this.name
  }
}

export class ChoiceElementType extends FormElementType {
  static getType() {
    return 'choice'
  }

  get name() {
    return this.app.i18n.t('elementType.choice')
  }

  get description() {
    return this.app.i18n.t('elementType.choiceDescription')
  }

  get iconClass() {
    return 'iconoir-list-select'
  }

  get component() {
    return ChoiceElement
  }

  get generalFormComponent() {
    return ChoiceElementForm
  }

  formDataType(element) {
    return element.multiple ? 'array' : 'string'
  }

  getInitialFormDataValue(element, applicationContext) {
    try {
      return ensureString(
        this.resolveFormula(element.default_value, {
          element,
          ...applicationContext,
        })
      )
    } catch {
      return element.multiple ? [] : ''
    }
  }

  getDisplayName(element, applicationContext) {
    const displayValue =
      element.label || element.default_value || element.placeholder

    if (displayValue) {
      const resolvedName = ensureString(
        this.resolveFormula(displayValue, applicationContext)
      ).trim()
      return resolvedName || this.name
    }
    return this.name
  }

  /**
   * Given a Choice Element, return an array of all valid option Values.
   *
   * When adding a new Option, the Page Designer can choose to only define the
   * Name and leave the Value undefined. In that case, the AB will assume the
   * Value to be the same as the Name. In the backend, the Value is stored as
   * null while the frontend visually displays the Name in its place.
   *
   * This means that an option's Value can sometimes be null. This method
   * gathers all valid Values. When a Value null, the Name is used instead.
   * Otherwise, the Value itself is used.
   *
   * @param element - The choice form element
   * @returns {Array} - An array of valid Values
   */
  choiceOptions(element) {
    return element.options.map((option) => {
      return option.value !== null ? option.value : option.name
    })
  }

  /**
   * Responsible for validating the choice form element. It behaves slightly
   * differently so that choice options with blank values are valid. We simply
   * test if the value is one of the choice's own values.
   * @param element - The choice form element
   * @param value - The value we are validating.
   * @param applicationContext - Required when using formula resolution.
   * @returns {boolean}
   */
  isValid(element, value, applicationContext) {
    const options =
      element.option_type === CHOICE_OPTION_TYPES.FORMULAS
        ? ensureArray(
            this.resolveFormula(element.formula_value, {
              element,
              ...applicationContext,
            })
          ).map(ensureString)
        : this.choiceOptions(element)

    const validOption = element.multiple
      ? options.some((option) => value.includes(option))
      : options.includes(value)

    return !(element.required && !validOption)
  }

  isInError({ element, builder }) {
    switch (element.option_type) {
      case CHOICE_OPTION_TYPES.MANUAL:
        return element.options.length === 0
      case CHOICE_OPTION_TYPES.FORMULAS: {
        return element.formula_value === ''
      }
      default:
        return true
    }
  }

  getDataSchema(element) {
    const type = this.formDataType(element)
    if (type === 'string') {
      return {
        type: 'string',
      }
    } else if (type === 'array') {
      return {
        type: 'array',
        items: {
          type: 'string',
        },
      }
    }
  }
}

export class CheckboxElementType extends FormElementType {
  static getType() {
    return 'checkbox'
  }

  get name() {
    return this.app.i18n.t('elementType.checkbox')
  }

  get description() {
    return this.app.i18n.t('elementType.checkboxDescription')
  }

  get iconClass() {
    return 'iconoir-check'
  }

  get component() {
    return CheckboxElement
  }

  get generalFormComponent() {
    return CheckboxElementForm
  }

  formDataType(element) {
    return 'boolean'
  }

  getInitialFormDataValue(element, applicationContext) {
    try {
      return ensureBoolean(
        this.resolveFormula(element.default_value, {
          element,
          ...applicationContext,
        })
      )
    } catch {
      return false
    }
  }
}

export class IFrameElementType extends ElementType {
  static getType() {
    return 'iframe'
  }

  get name() {
    return this.app.i18n.t('elementType.iframe')
  }

  get description() {
    return this.app.i18n.t('elementType.iframeDescription')
  }

  get iconClass() {
    return 'iconoir-app-window'
  }

  get component() {
    return IFrameElement
  }

  get generalFormComponent() {
    return IFrameElementForm
  }

  getDisplayName(element, applicationContext) {
    if (element.url && element.url.length) {
      const resolvedName = ensureString(
        this.resolveFormula(element.url, applicationContext)
      )
      return resolvedName || this.name
    }
    return this.name
  }
}

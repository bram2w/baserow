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

import { ELEMENT_EVENTS } from '@baserow/modules/builder/enums'
import {
  ensureBoolean,
  ensureString,
} from '@baserow/modules/core/utils/validator'
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
import DropdownElement from '@baserow/modules/builder/components/elements/components/DropdownElement.vue'
import DropdownElementForm from '@baserow/modules/builder/components/elements/components/forms/general/DropdownElementForm.vue'
import CheckboxElement from '@baserow/modules/builder/components/elements/components/CheckboxElement.vue'
import CheckboxElementForm from '@baserow/modules/builder/components/elements/components/forms/general/CheckboxElementForm.vue'
import IFrameElement from '@baserow/modules/builder/components/elements/components/IFrameElement.vue'
import IFrameElementForm from '@baserow/modules/builder/components/elements/components/forms/general/IFrameElementForm.vue'
import { pathParametersInError } from '@baserow/modules/builder/utils/params'

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
      'style_border_top',
      'style_border_bottom',
      'style_border_left',
      'style_border_right',
      'style_background',
      'style_background_color',
      'style_width',
    ]
  }

  get styles() {
    return this.stylesAll
  }

  get events() {
    return []
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

  getEvents() {
    return this.events.map((EventType) => new EventType(this.app))
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
}

export class ContainerElementType extends ElementType {
  get elementTypesAll() {
    return Object.values(this.app.$registry.getAll('element'))
  }

  /**
   * Returns an array of element types that are not allowed as children of this element.
   *
   * @returns {Array}
   */
  get childElementTypesForbidden() {
    return []
  }

  get childElementTypes() {
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
    // By default an element inside a container should have no left and right padding
    return { style_padding_left: 0, style_padding_right: 0 }
  }
}

export class ColumnElementType extends ContainerElementType {
  getType() {
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

  get childElementTypesForbidden() {
    return this.elementTypesAll.filter(
      (elementType) => elementType instanceof ContainerElementType
    )
  }

  get childStylesForbidden() {
    return ['style_width']
  }

  get defaultPlaceInContainer() {
    return '0'
  }
}

/**
 * This class servers as a parent class for all form element types. Form element types
 * are all elements that can be used as part of a form. So in simple terms, any element
 * that can represents data in a way that is directly modifiable by an application user.
 */
export class FormElementType extends ElementType {
  isFormElement = true

  get formDataType() {
    return null
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

  afterCreate(element, page) {
    const payload = {
      value: this.getInitialFormDataValue(element, { page }),
      type: this.formDataType,
    }

    return this.app.store.dispatch('formData/setFormData', {
      page,
      payload,
      elementId: element.id,
    })
  }

  afterDelete(element, page) {
    return this.app.store.dispatch('formData/removeFormData', {
      page,
      elementId: element.id,
    })
  }
}

export class InputTextElementType extends FormElementType {
  getType() {
    return 'input_text'
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

  get formDataType() {
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
    return this.resolveFormula(element.default_value, {
      element,
      ...applicationContext,
    })
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
  getType() {
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
  getType() {
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

  get events() {
    return [ClickEvent]
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

export class TableElementType extends ElementType {
  getType() {
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
}

export class DropdownElementType extends FormElementType {
  static getType() {
    return 'dropdown'
  }

  get name() {
    return this.app.i18n.t('elementType.dropdown')
  }

  get description() {
    return this.app.i18n.t('elementType.dropdownDescription')
  }

  get iconClass() {
    return 'iconoir-list-select'
  }

  get component() {
    return DropdownElement
  }

  get generalFormComponent() {
    return DropdownElementForm
  }

  get formDataType() {
    return 'string'
  }

  getInitialFormDataValue(element, applicationContext) {
    return this.resolveFormula(element.default_value, {
      element,
      ...applicationContext,
    })
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
}

export class FormContainerElementType extends ContainerElementType {
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

  get childElementTypesForbidden() {
    return this.elementTypesAll.filter((type) => !type.isFormElement)
  }

  get events() {
    return [SubmitEvent]
  }

  get childStylesForbidden() {
    return ['style_width']
  }
}

export class CheckboxElementType extends FormElementType {
  getType() {
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

  get formDataType() {
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
  getType() {
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

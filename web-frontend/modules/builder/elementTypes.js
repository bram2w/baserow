import { Registerable } from '@baserow/modules/core/registry'
import ParagraphElement from '@baserow/modules/builder/components/elements/components/ParagraphElement'
import HeadingElement from '@baserow/modules/builder/components/elements/components/HeadingElement'
import LinkElement from '@baserow/modules/builder/components/elements/components/LinkElement'
import LinkElementEdit from '@baserow/modules/builder/components/elements/components/LinkElementEdit'
import ParagraphElementForm from '@baserow/modules/builder/components/elements/components/forms/ParagraphElementForm'
import HeadingElementForm from '@baserow/modules/builder/components/elements/components/forms/HeadingElementForm'
import LinkElementForm from '@baserow/modules/builder/components/elements/components/forms/LinkElementForm'
import ImageElementForm from '@baserow/modules/builder/components/elements/components/forms/ImageElementForm'
import ImageElement from '@baserow/modules/builder/components/elements/components/ImageElement'

import { compile } from 'path-to-regexp'
import { PAGE_PARAM_TYPE_VALIDATION_FUNCTIONS } from '@baserow/modules/builder/enums'

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

  get formComponent() {
    return null
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
   * This hook allows you to change the values given by the form of the element before
   * they are sent to the backend to update the element.
   *
   * @param {object} values - The values of the element
   * @returns {*}
   */
  prepareValuesForRequest(values) {
    return values
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
    return 'heading'
  }

  get component() {
    return HeadingElement
  }

  get formComponent() {
    return HeadingElementForm
  }
}

export class ParagraphElementType extends ElementType {
  static getType() {
    return 'paragraph'
  }

  get name() {
    return this.app.i18n.t('elementType.paragraph')
  }

  get description() {
    return this.app.i18n.t('elementType.paragraphDescription')
  }

  get iconClass() {
    return 'paragraph'
  }

  get component() {
    return ParagraphElement
  }

  get formComponent() {
    return ParagraphElementForm
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
    return 'link'
  }

  get component() {
    return LinkElement
  }

  get editComponent() {
    return LinkElementEdit
  }

  get formComponent() {
    return LinkElementForm
  }

  isInError({ element, builder }) {
    try {
      LinkElementType.getUrlFromElement(element, builder)
    } catch (e) {
      // Error in path resolution
      return true
    }

    return LinkElementType.arePathParametersInError(element, builder)
  }

  static validatePathParamType(value, type) {
    const validationFunction = PAGE_PARAM_TYPE_VALIDATION_FUNCTIONS[type]
    return validationFunction !== undefined && validationFunction(value)
  }

  static arePathParametersInError(element, builder) {
    if (
      element.navigation_type === 'page' &&
      !isNaN(element.navigate_to_page_id)
    ) {
      const destinationPage = builder.pages.find(
        ({ id }) => id === element.navigate_to_page_id
      )

      if (destinationPage) {
        const destinationPageParams = destinationPage.path_params || []
        const pageParams = element.page_parameters || []

        if (destinationPageParams.length !== pageParams.length) {
          return true
        }

        for (let i = 0; i < destinationPageParams.length; i++) {
          const destinationParam = destinationPageParams[i]
          const pageParam = pageParams[i]

          if (
            destinationParam.name !== pageParam.name ||
            !LinkElementType.validatePathParamType(
              pageParam.value,
              destinationParam.type
            )
          ) {
            return true
          }
        }
      }
    }

    return false
  }

  static getUrlFromElement(element, builder) {
    if (element.navigation_type === 'page') {
      if (!isNaN(element.navigate_to_page_id)) {
        const page = builder.pages.find(
          ({ id }) => id === element.navigate_to_page_id
        )

        // The builder page list might be empty or the page has been deleted
        if (!page) {
          return ''
        }

        const toPath = compile(page.path, { encode: encodeURIComponent })
        const pageParams = Object.fromEntries(
          element.page_parameters.map(({ name, value }) => [name, value])
        )
        return toPath(pageParams)
      }
    } else if (!element.navigate_to_url.startsWith('http')) {
      // add the https protocol if missing
      return `https://${element.navigate_to_url}`
    } else {
      return element.navigate_to_url
    }
    return ''
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
    return 'image'
  }

  get component() {
    return ImageElement
  }

  get formComponent() {
    return ImageElementForm
  }

  prepareValuesForRequest(values) {
    // We only want to send the name of the image file instead of the entire object
    // since we only need to link the image file to the element and not copy the entire
    // data structure.
    if (values.image_file) {
      values.image_file_id = values.image_file.id
      delete values.image_file
    } else {
      delete values.image_file_id
    }
    return values
  }
}

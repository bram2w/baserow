import { Registerable } from '@baserow/modules/core/registry'
import ParagraphElement from '@baserow/modules/builder/components/elements/components/ParagraphElement'
import HeadingElement from '@baserow/modules/builder/components/elements/components/HeadingElement'

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

  get properties() {
    return []
  }

  /**
   * Extracts the attributes of the element instance into attributes that the component
   * can use. The returned object needs to be a mapping from the name of the property
   * at the component level to the value in the element object.
   *
   * Example:
   * - Let's say you have a prop called `level`
   * - The element looks like this: { 'id': 'someId', 'level': 1 }
   *
   * Then you will have to return { 'level': element.level }
   *
   * @param element
   * @returns {{}}
   */
  getComponentProps(element) {
    return {}
  }
}

export class HeadingElementType extends ElementType {
  getType() {
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

  getComponentProps(element) {
    return {
      value: 'some test value for now',
      level: element.level,
    }
  }
}

export class ParagraphElementType extends ElementType {
  getType() {
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

  getComponentProps(element) {
    return {
      value: 'some test value for now',
    }
  }
}

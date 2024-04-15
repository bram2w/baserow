import { Registerable } from '@baserow/modules/core/registry'
import TextField from '@baserow/modules/builder/components/elements/components/collectionField/TextField'
import LinkField from '@baserow/modules/builder/components/elements/components/collectionField/LinkField'
import TextFieldForm from '@baserow/modules/builder/components/elements/components/collectionField/form/TextFieldForm'
import LinkFieldForm from '@baserow/modules/builder/components/elements/components/collectionField/form/LinkFieldForm'
import { ensureString } from '@baserow/modules/core/utils/validator'
import resolveElementUrl from '@baserow/modules/builder/utils/urlResolution'
import { pathParametersInError } from '@baserow/modules/builder/utils/params'

export class CollectionFieldType extends Registerable {
  get name() {
    return null
  }

  get component() {
    return null
  }

  get formComponent() {
    return null
  }

  getProps(field, { resolveFormula, applicationContext }) {
    return {}
  }

  getOrder() {
    return 50
  }

  /**
   * Returns whether the collection field configuration is valid or not.
   * @param {object} param An object containing the collection field and the builder
   * @returns true if the collection field is in error
   */
  isInError({ field, builder }) {
    return false
  }
}

export class TextCollectionFieldType extends CollectionFieldType {
  static getType() {
    return 'text'
  }

  get name() {
    return this.app.i18n.t('collectionFieldType.text')
  }

  get component() {
    return TextField
  }

  get formComponent() {
    return TextFieldForm
  }

  getProps(field, { resolveFormula, applicationContext }) {
    return { value: ensureString(resolveFormula(field.value)) }
  }

  getOrder() {
    return 10
  }
}

export class LinkCollectionFieldType extends CollectionFieldType {
  static getType() {
    return 'link'
  }

  get name() {
    return this.app.i18n.t('collectionFieldType.link')
  }

  get component() {
    return LinkField
  }

  get formComponent() {
    return LinkFieldForm
  }

  getProps(field, { resolveFormula, applicationContext: { mode, builder } }) {
    const defaultProps = {
      url: '',
      navigationType: field.navigation_type || '',
      linkName: ensureString(resolveFormula(field.link_name)),
      target: field.target || 'self',
    }
    try {
      return {
        ...defaultProps,
        url: resolveElementUrl(field, builder, resolveFormula, mode),
      }
    } catch (error) {
      return defaultProps
    }
  }

  getOrder() {
    return 20
  }

  /**
   * Returns whether the link field configuration has parameters in error or not.
   * @param {object} param An object containing the link field and the builder
   * @returns true if the link field is in error
   */
  isInError({ field, builder }) {
    return pathParametersInError(field, builder)
  }
}

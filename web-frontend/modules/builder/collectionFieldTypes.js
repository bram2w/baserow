import { Registerable } from '@baserow/modules/core/registry'
import TextField from '@baserow/modules/builder/components/elements/components/collectionField/TextField'
import LinkField from '@baserow/modules/builder/components/elements/components/collectionField/LinkField'
import TextFieldForm from '@baserow/modules/builder/components/elements/components/collectionField/form/TextFieldForm'
import LinkFieldForm from '@baserow/modules/builder/components/elements/components/collectionField/form/LinkFieldForm'
import { ensureString } from '@baserow/modules/core/utils/validator'
import resolveElementUrl from '@baserow/modules/builder/utils/urlResolution'

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
      isExternalLink: false,
      navigationType: field.navigation_type,
      linkName: ensureString(resolveFormula(field.link_name)),
    }
    try {
      const resolvedUrlContext = resolveElementUrl(
        field,
        builder,
        resolveFormula,
        mode
      )
      return { ...defaultProps, ...resolvedUrlContext }
    } catch (error) {
      return defaultProps
    }
  }

  getOrder() {
    return 20
  }
}

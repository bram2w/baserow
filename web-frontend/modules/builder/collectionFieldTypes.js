import { Registerable } from '@baserow/modules/core/registry'
import TextField from '@baserow/modules/builder/components/elements/components/collectionField/TextField'
import LinkField from '@baserow/modules/builder/components/elements/components/collectionField/LinkField'
import TextFieldForm from '@baserow/modules/builder/components/elements/components/collectionField/form/TextFieldForm'
import LinkFieldForm from '@baserow/modules/builder/components/elements/components/collectionField/form/LinkFieldForm'
import { ensureString } from '@baserow/modules/core/utils/validator'

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

  getProps(field, { resolveFormula }) {
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

  getProps(field, { resolveFormula }) {
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

  getProps(field, { resolveFormula }) {
    return {
      url: ensureString(resolveFormula(field.url)),
      linkName: ensureString(resolveFormula(field.link_name)),
    }
  }

  getOrder() {
    return 20
  }
}

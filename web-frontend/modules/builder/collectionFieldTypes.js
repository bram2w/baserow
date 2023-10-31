import { Registerable } from '@baserow/modules/core/registry'
import TextField from '@baserow/modules/builder/components/elements/components/collectionField/TextField'
import LinkField from '@baserow/modules/builder/components/elements/components/collectionField/LinkField'
import TextFieldForm from '@baserow/modules/builder/components/elements/components/collectionField/form/TextFieldForm'
import LinkFieldForm from '@baserow/modules/builder/components/elements/components/collectionField/form/LinkFieldForm'

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

  getOrder() {
    return 20
  }
}

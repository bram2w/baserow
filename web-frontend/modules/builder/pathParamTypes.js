import { Registerable } from '@baserow/modules/core/registry'

export class PathParamType extends Registerable {
  get name() {
    return null
  }
}

export class TextPathParamType extends PathParamType {
  static getType() {
    return 'text'
  }

  getOrder() {
    return 10
  }

  get name() {
    return this.app.i18n.t('pathParamTypes.textName')
  }
}

export class NumericPathParamType extends PathParamType {
  static getType() {
    return 'numeric'
  }

  getOrder() {
    return 20
  }

  get name() {
    return this.app.i18n.t('pathParamTypes.numericName')
  }
}

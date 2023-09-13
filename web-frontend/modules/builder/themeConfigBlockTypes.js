import { Registerable } from '@baserow/modules/core/registry'
import MainThemeConfigBlockComponent from '@baserow/modules/builder/components/theme/MainThemeConfigBlock'

export class ThemeConfigBlockType extends Registerable {
  static getType() {
    return null
  }

  get component() {
    return null
  }
}

export class MainThemeConfigBlock extends ThemeConfigBlockType {
  static getType() {
    return 'main'
  }

  get component() {
    return MainThemeConfigBlockComponent
  }
}

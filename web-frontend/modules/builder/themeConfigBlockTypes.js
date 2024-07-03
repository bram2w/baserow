import { Registerable } from '@baserow/modules/core/registry'
import ColorThemeConfigBlock from '@baserow/modules/builder/components/theme/ColorThemeConfigBlock'
import TypographyThemeConfigBlock from '@baserow/modules/builder/components/theme/TypographyThemeConfigBlock'
import ButtonThemeConfigBlock from '@baserow/modules/builder/components/theme/ButtonThemeConfigBlock'
import { resolveColor } from '@baserow/modules/core/utils/colors'

/**
 * Helper class to construct easily style objects.
 */
export class ThemeStyle {
  constructor() {
    this.style = {}
  }

  addIfExists(theme, propName, styleName, transform = (v) => v) {
    if (Object.prototype.hasOwnProperty.call(theme, propName)) {
      this.style[styleName] = transform(theme[propName])
    }
  }

  toObject() {
    return this.style
  }
}

export class ThemeConfigBlockType extends Registerable {
  get label() {
    return null
  }

  /**
   * Return the CSS to apply for the theme config block. Essentially it's mainly
   * definitions of a bunch of CSS vars that are used by the ABComponents to style
   * themselves.
   *
   * @param {Object} theme the theme to use to populate the CSS vars.
   * @param {Array} colorVariables the color variable mapping.
   * @returns an object that can be use as style property for a DOM element
   */
  getCSS(theme, colorVariables) {
    return null
  }

  /**
   * Returns the color variables provided by this theme config block. These variables
   * can then be used by other theme block properties.
   *
   * @param {Object} theme the theme object that contains the value definitions.
   * @returns An array of color variables.
   */
  getColorVariables(theme) {
    return []
  }

  /**
   * Returns the component to configure this theme block.
   */
  get component() {
    return null
  }

  /**
   * Iterate over the registered theme blocks to generate the full CSS style object.
   * This object can then be used to style the application.
   *
   * @param {Array} themeBlocks the list of themeBlocks to consider.
   * @param {Object} theme the theme of the application.
   * @param {Array} colorVariables the color variables array.
   * @returns
   */
  static getAllStyles(themeBlocks, theme, colorVariables = null) {
    if (colorVariables === null) {
      colorVariables = this.getAllColorVariables(themeBlocks, theme)
    }
    return themeBlocks
      .map((block) => block.getCSS(theme, colorVariables))
      .reduce((acc, obj) => ({ ...acc, ...obj }), {})
  }

  /**
   * Get all variables from all theme blocks.
   *
   * @param {Array} themeBlocks theme blocks to consider
   * @param {Object} theme theme of the application
   * @returns the color variables array
   */
  static getAllColorVariables(themeBlocks, theme) {
    return themeBlocks.map((block) => block.getColorVariables(theme)).flat()
  }

  getOrder() {
    return 50
  }
}

export class ColorThemeConfigBlockType extends ThemeConfigBlockType {
  static getType() {
    return 'color'
  }

  get label() {
    return this.app.i18n.t('themeConfigBlockType.color')
  }

  getCSS(theme, colorVariables) {
    const style = new ThemeStyle()
    style.addIfExists(theme, 'primary_color', '--primary-color')
    style.addIfExists(theme, 'secondary_color', '--secondary-color')
    style.addIfExists(theme, 'border_color', '--border-color')
    return style.toObject()
  }

  getColorVariables(theme) {
    const { i18n } = this.app
    return [
      {
        name: i18n.t('colorThemeConfigBlockType.primary'),
        value: 'primary',
        color: theme.primary_color,
      },
      {
        name: i18n.t('colorThemeConfigBlockType.secondary'),
        value: 'secondary',
        color: theme.secondary_color,
      },
      {
        name: i18n.t('colorThemeConfigBlockType.border'),
        value: 'border',
        color: theme.border_color,
      },
    ]
  }

  get component() {
    return ColorThemeConfigBlock
  }

  getOrder() {
    return 10
  }
}

export class TypographyThemeConfigBlockType extends ThemeConfigBlockType {
  static getType() {
    return 'typography'
  }

  get label() {
    return this.app.i18n.t('themeConfigBlockType.typography')
  }

  getCSS(theme, colorVariables) {
    const style = new ThemeStyle()
    Array.from([1, 2, 3, 4, 5, 6]).forEach((level) => {
      style.addIfExists(
        theme,
        `heading_${level}_font_size`,
        `--heading-h${level}-font-size`,
        (v) => `${Math.min(100, v)}px`
      )
      style.addIfExists(
        theme,
        `heading_${level}_text_color`,
        `--heading-h${level}-color`,
        (v) => resolveColor(v, colorVariables)
      )
    })
    return style.toObject()
  }

  get component() {
    return TypographyThemeConfigBlock
  }

  getOrder() {
    return 20
  }
}

export class ButtonThemeConfigBlockType extends ThemeConfigBlockType {
  static getType() {
    return 'button'
  }

  get label() {
    return this.app.i18n.t('themeConfigBlockType.button')
  }

  getCSS(theme, colorVariables) {
    const style = new ThemeStyle()
    style.addIfExists(theme, 'button_background_color', '--button-color', (v) =>
      resolveColor(v, colorVariables)
    )
    style.addIfExists(
      theme,
      'button_hover_background_color',
      '--hover-button-color',
      (v) => resolveColor(v, colorVariables)
    )
    return style.toObject()
  }

  get component() {
    return ButtonThemeConfigBlock
  }

  getOrder() {
    return 40
  }
}

import { Registerable } from '@baserow/modules/core/registry'
import ColorThemeConfigBlock from '@baserow/modules/builder/components/theme/ColorThemeConfigBlock'
import TypographyThemeConfigBlock from '@baserow/modules/builder/components/theme/TypographyThemeConfigBlock'
import ButtonThemeConfigBlock from '@baserow/modules/builder/components/theme/ButtonThemeConfigBlock'
import LinkThemeConfigBlock from '@baserow/modules/builder/components/theme/LinkThemeConfigBlock'
import ImageThemeConfigBlock from '@baserow/modules/builder/components/theme/ImageThemeConfigBlock'
import PageThemeConfigBlock from '@baserow/modules/builder/components/theme/PageThemeConfigBlock'
import { resolveColor } from '@baserow/modules/core/utils/colors'
import {
  WIDTHS_NEW,
  HORIZONTAL_ALIGNMENTS,
  BACKGROUND_MODES,
} from '@baserow/modules/builder/enums'
import get from 'lodash/get'

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
  getCSS(theme, colorVariables, baseTheme = null) {
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
  static getAllStyles(
    themeBlocks,
    theme,
    colorVariables = null,
    baseTheme = null
  ) {
    if (colorVariables === null) {
      colorVariables = this.getAllColorVariables(themeBlocks, theme)
    }
    return (
      themeBlocks
        .map((block) => block.getCSS(theme, colorVariables, baseTheme))
        // Flatten the array of objects
        .reduce((acc, obj) => ({ ...acc, ...obj }), {})
    )
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

  getCSS(theme, colorVariables, baseTheme = null) {
    return {}
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
      {
        name: i18n.t('colorThemeConfigBlockType.success'),
        value: 'success',
        color: theme.main_success_color,
      },
      {
        name: i18n.t('colorThemeConfigBlockType.warning'),
        value: 'warning',
        color: theme.main_warning_color,
      },
      {
        name: i18n.t('colorThemeConfigBlockType.error'),
        value: 'error',
        color: theme.main_error_color,
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

  getCSS(theme, colorVariables, baseTheme = null) {
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
      style.addIfExists(
        theme,
        `heading_${level}_text_alignment`,
        `--heading-h${level}-text-alignment`,
        (v) => v
      )
      style.addIfExists(
        theme,
        `heading_${level}_font_family`,
        `--heading-h${level}-font-family`,
        (v) => {
          const fontFamilyType = this.app.$registry.get('fontFamily', v)
          return `"${fontFamilyType.name}","${fontFamilyType.safeFont}"`
        }
      )
    })
    style.addIfExists(
      theme,
      `body_font_size`,
      `--body-font-size`,
      (v) => `${Math.min(100, v)}px`
    )
    style.addIfExists(theme, `body_text_color`, `--body-text-color`, (v) =>
      resolveColor(v, colorVariables)
    )
    style.addIfExists(
      theme,
      `body_text_alignment`,
      `--body-text-alignment`,
      (v) => v
    )
    style.addIfExists(theme, `body_font_family`, `--body-font-family`, (v) => {
      const fontFamilyType = this.app.$registry.get('fontFamily', v)
      return `"${fontFamilyType.name}","${fontFamilyType.safeFont}"`
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

  getCSS(theme, colorVariables, baseTheme = null) {
    const style = new ThemeStyle()
    style.addIfExists(
      theme,
      'button_background_color',
      '--button-background-color',
      (v) => resolveColor(v, colorVariables)
    )
    style.addIfExists(
      theme,
      'button_hover_background_color',
      '--button-hover-background-color',
      (v) => resolveColor(v, colorVariables)
    )
    style.addIfExists(theme, 'button_text_color', '--button-text-color', (v) =>
      resolveColor(v, colorVariables)
    )
    style.addIfExists(
      theme,
      'button_hover_text_color',
      '--button-hover-text-color',
      (v) => resolveColor(v, colorVariables)
    )
    style.addIfExists(
      theme,
      'button_border_color',
      '--button-border-color',
      (v) => resolveColor(v, colorVariables)
    )
    style.addIfExists(
      theme,
      'button_hover_border_color',
      '--button-hover-border-color',
      (v) => resolveColor(v, colorVariables)
    )
    style.addIfExists(theme, 'button_width', '--button-width', (v) =>
      v === WIDTHS_NEW.FULL ? '100%' : 'auto'
    )
    style.addIfExists(
      theme,
      'button_text_alignment',
      '--button-text-alignment',
      (v) => v
    )
    style.addIfExists(
      theme,
      'button_alignment',
      '--button-alignment',
      (v) =>
        ({
          [HORIZONTAL_ALIGNMENTS.LEFT]: 'flex-start',
          [HORIZONTAL_ALIGNMENTS.CENTER]: 'center',
          [HORIZONTAL_ALIGNMENTS.RIGHT]: 'flex-end',
        }[v])
    )
    style.addIfExists(
      theme,
      'button_font_alignment',
      '--button-text-alignment',
      (v) => v
    )
    style.addIfExists(
      theme,
      `button_font_family`,
      `--button-font-family`,
      (v) => {
        const fontFamilyType = this.app.$registry.get('fontFamily', v)
        return `"${fontFamilyType.name}","${fontFamilyType.safeFont}"`
      }
    )
    style.addIfExists(
      theme,
      `button_font_size`,
      `--button-font-size`,
      (v) => `${Math.min(100, v)}px`
    )
    style.addIfExists(
      theme,
      `button_border_radius`,
      `--button-border-radius`,
      (v) => `${v}px`
    )
    style.addIfExists(
      theme,
      `button_border_size`,
      `--button-border-size`,
      (v) => `${v}px`
    )
    style.addIfExists(
      theme,
      `button_horizontal_padding`,
      `--button-horizontal-padding`,
      (v) => `${v}px`
    )
    style.addIfExists(
      theme,
      `button_vertical_padding`,
      `--button-vertical-padding`,
      (v) => `${v}px`
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

export class LinkThemeConfigBlockType extends ThemeConfigBlockType {
  static getType() {
    return 'link'
  }

  get label() {
    return this.app.i18n.t('themeConfigBlockType.link')
  }

  getCSS(theme, colorVariables, baseTheme = null) {
    const style = new ThemeStyle()
    style.addIfExists(theme, 'link_text_color', '--link-text-color', (v) =>
      resolveColor(v, colorVariables)
    )
    style.addIfExists(
      theme,
      'link_hover_text_color',
      '--link-hover-text-color',
      (v) => resolveColor(v, colorVariables)
    )
    style.addIfExists(
      theme,
      'link_text_alignment',
      '--link-text-alignment',
      (v) =>
        ({
          [HORIZONTAL_ALIGNMENTS.LEFT]: 'flex-start',
          [HORIZONTAL_ALIGNMENTS.CENTER]: 'center',
          [HORIZONTAL_ALIGNMENTS.RIGHT]: 'flex-end',
        }[v])
    )
    style.addIfExists(theme, `link_font_family`, `--link-font-family`, (v) => {
      const fontFamilyType = this.app.$registry.get('fontFamily', v)
      return `"${fontFamilyType.name}","${fontFamilyType.safeFont}"`
    })
    return style.toObject()
  }

  get component() {
    return LinkThemeConfigBlock
  }

  getOrder() {
    return 50
  }
}

export class ImageThemeConfigBlockType extends ThemeConfigBlockType {
  static getType() {
    return 'image'
  }

  get label() {
    return this.app.i18n.t('themeConfigBlockType.image')
  }

  getCSS(theme, colorVariables, baseTheme = null) {
    const style = new ThemeStyle()
    style.addIfExists(
      theme,
      'image_alignment',
      '--image-alignment',
      (v) =>
        ({
          [HORIZONTAL_ALIGNMENTS.LEFT]: 'flex-start',
          [HORIZONTAL_ALIGNMENTS.CENTER]: 'center',
          [HORIZONTAL_ALIGNMENTS.RIGHT]: 'flex-end',
        }[v])
    )

    const imageMaxWidth = get(
      theme,
      'image_max_width',
      baseTheme?.image_max_width
    )
    const imageMaxHeight = get(
      theme,
      'image_max_height',
      baseTheme?.image_max_height
    )
    const imageConstraint = get(
      theme,
      'image_constraint',
      baseTheme?.image_constraint
    )

    if (Object.prototype.hasOwnProperty.call(theme, 'image_max_width')) {
      style.style['--image-wrapper-width'] = `${imageMaxWidth}%`
      style.style['--image-wrapper-max-width'] = `${imageMaxWidth}%`
    }

    if (Object.prototype.hasOwnProperty.call(theme, 'image_max_height')) {
      if (imageMaxHeight) {
        style.style['--image-max-width'] = 'auto'
        style.style['--image-wrapper-max-height'] = `${imageMaxHeight}px`
      } else if (baseTheme?.image_max_height) {
        style.style['--image-wrapper-max-height'] = 'none'
      }
    }

    if (Object.prototype.hasOwnProperty.call(theme, 'image_constraint')) {
      switch (imageConstraint) {
        case 'cover':
          style.style['--image-wrapper-width'] = '100%'
          style.style['--image-object-fit'] = 'cover'
          style.style['--image-width'] = '100%'
          style.style['--image-height'] = '100%'
          break
        case 'contain':
          style.style['--image-object-fit'] = 'contain'
          style.style['--image-max-width'] = '100%'
          break
        case 'full-width':
          style.style['--image-object-fit'] = 'fill'
          style.style['--image-width'] = '100%'
          style.style['--image-height'] = '100%'
          style.style['--image-max-width'] = 'none'
          break
      }
    }

    return style.toObject()
  }

  get component() {
    return ImageThemeConfigBlock
  }

  getOrder() {
    return 60
  }
}

export class PageThemeConfigBlockType extends ThemeConfigBlockType {
  static getType() {
    return 'page'
  }

  get label() {
    return this.app.i18n.t('themeConfigBlockType.page')
  }

  getCSS(theme, colorVariables, baseTheme = null) {
    const style = new ThemeStyle()
    style.addIfExists(
      theme,
      'page_background_color',
      '--page-background-color',
      (v) => resolveColor(v, colorVariables)
    )
    style.addIfExists(
      theme,
      'page_background_file',
      '--page-background-image',
      (v) => (v ? `url(${v.url})` : 'none')
    )
    if (theme.page_background_mode === BACKGROUND_MODES.FILL) {
      style.style['--page-background-size'] = 'cover'
      style.style['--page-background-repeat'] = 'no-repeat'
    }
    if (theme.page_background_mode === BACKGROUND_MODES.TILE) {
      style.style['--page-background-size'] = 'auto'
      style.style['--page-background-repeat'] = 'repeat'
    }
    if (theme.page_background_mode === BACKGROUND_MODES.FIT) {
      style.style['--page-background-size'] = 'contain'
      style.style['--page-background-repeat'] = 'no-repeat'
    }
    return style.toObject()
  }

  get component() {
    return PageThemeConfigBlock
  }

  getOrder() {
    return 15
  }
}

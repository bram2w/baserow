import {
  ensureInteger,
  ensureString,
} from '@baserow/modules/core/utils/validator'
import {
  DataSourceDataProviderType,
  PageParameterDataProviderType,
} from '@baserow/modules/builder/dataProviderTypes'

export const PLACEMENTS = {
  BEFORE: 'before',
  AFTER: 'after',
  LEFT: 'left',
  RIGHT: 'right',
}
export const PAGE_PARAM_TYPE_VALIDATION_FUNCTIONS = {
  numeric: ensureInteger,
  text: ensureString,
}

export const IMAGE_SOURCE_TYPES = {
  UPLOAD: 'upload',
  URL: 'url',
}

export const HORIZONTAL_ALIGNMENTS = {
  LEFT: {
    name: 'horizontalAlignmentSelector.alignmentLeft',
    value: 'left',
    icon: 'iconoir-align-left',
  },
  CENTER: {
    name: 'horizontalAlignmentSelector.alignmentCenter',
    value: 'center',
    icon: 'iconoir-align-center',
  },
  RIGHT: {
    name: 'horizontalAlignmentSelector.alignmentRight',
    value: 'right',
    icon: 'iconoir-align-right',
  },
}

export const VERTICAL_ALIGNMENTS = {
  TOP: {
    name: 'verticalAlignmentSelector.alignmentTop',
    value: 'iconoir-align-top-box',
  },
  CENTER: {
    name: 'verticalAlignmentSelector.alignmentCenter',
    value: 'iconoir-center-align',
  },
  BOTTOM: {
    name: 'verticalAlignmentSelector.alignmentBottom',
    value: 'iconoir-align-bottom-box',
  },
}

export const WIDTHS = {
  AUTO: { value: 'auto', name: 'widthSelector.widthAuto' },
  FULL: { value: 'full', name: 'widthSelector.widthFull' },
}

/**
 * A list of all the data providers that can be used in the formula field on the right
 * sidebar in the application builder.
 *
 * @type {String[]}
 */
export const DATA_PROVIDERS_ALLOWED_SIDEBAR = [
  new DataSourceDataProviderType().getType(),
  new PageParameterDataProviderType().getType(),
]

/**
 * A list of all the data provider that can be used to configure data sources.
 *
 * @type {String[]}
 */
export const DATA_PROVIDERS_ALLOWED_DATA_SOURCES = [
  new PageParameterDataProviderType().getType(),
]

import {
  ensureInteger,
  ensureString,
} from '@baserow/modules/core/utils/validator'
import {
  DataSourceDataProviderType,
  PageParameterDataProviderType,
  CurrentRecordDataProviderType,
  FormDataProviderType,
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

export const BACKGROUND_TYPES = {
  NONE: { value: 'none', name: 'backgroundTypes.none' },
  COLOR: { value: 'color', name: 'backgroundTypes.color' },
}

export const WIDTH_TYPES = {
  FULL: { value: 'full', name: 'widthTypes.full' },
  NORMAL: { value: 'normal', name: 'widthTypes.normal' },
  MEDIUM: { value: 'medium', name: 'widthTypes.medium' },
  SMALL: { value: 'small', name: 'widthTypes.small' },
}

/**
 * A list of all the data providers that can be used in the formula field on the right
 * sidebar in the application builder.
 *
 * @type {String[]}
 */
export const DATA_PROVIDERS_ALLOWED_ELEMENTS = [
  CurrentRecordDataProviderType.getType(),
  PageParameterDataProviderType.getType(),
  DataSourceDataProviderType.getType(),
  FormDataProviderType.getType(),
]

/**
 * A list of all the data provider that can be used to configure data sources.
 *
 * @type {String[]}
 */
export const DATA_PROVIDERS_ALLOWED_DATA_SOURCES = [
  PageParameterDataProviderType.getType(),
]

export const ELEMENT_EVENTS = {
  DATA_SOURCE_REMOVED: 'DATA_SOURCE_REMOVED',
  DATA_SOURCE_AFTER_UPDATE: 'DATA_SOURCE_AFTER_UPDATE',
}

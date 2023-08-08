import {
  ensureInteger,
  ensureString,
} from '@baserow/modules/core/utils/validator'

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
    icon: 'align-left',
  },
  CENTER: {
    name: 'horizontalAlignmentSelector.alignmentCenter',
    value: 'center',
    icon: 'align-center',
  },
  RIGHT: {
    name: 'horizontalAlignmentSelector.alignmentRight',
    value: 'right',
    icon: 'align-right',
  },
}

export const VERTICAL_ALIGNMENTS = {
  TOP: {
    name: 'verticalAlignmentSelector.alignmentTop',
    value: 'top',
  },
  CENTER: {
    name: 'verticalAlignmentSelector.alignmentCenter',
    value: 'center',
  },
  BOTTOM: {
    name: 'verticalAlignmentSelector.alignmentBottom',
    value: 'bottom',
  },
}

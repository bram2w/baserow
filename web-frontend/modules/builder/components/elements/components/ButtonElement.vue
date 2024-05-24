<template>
  <div
    class="button-element"
    :class="classes"
    :style="{
      '--button-color': resolveColor(element.button_color, colorVariables),
    }"
  >
    <ABButton
      :full-width="element.width === WIDTHS.FULL.value"
      :loading="workflowActionsInProgress"
      @click="fireEvent(elementType.getEventByName(element, 'click'))"
    >
      {{ resolvedValue || $t('buttonElement.noValue') }}
    </ABButton>
  </div>
</template>

<script>
import element from '@baserow/modules/builder/mixins/element'
import { ensureString } from '@baserow/modules/core/utils/validator'
import { WIDTHS } from '@baserow/modules/builder/enums'

/**
 * @typedef ButtonElement
 * @property {string} value The text inside the button
 * @property {string} alignment left|center|right
 * @property {string} width auto|full
 */

export default {
  name: 'ButtonElement',
  mixins: [element],
  props: {
    /**
     * @type {ButtonElement}
     */
    element: {
      type: Object,
      required: true,
    },
  },
  computed: {
    WIDTHS: () => WIDTHS,
    resolvedValue() {
      try {
        return ensureString(this.resolveFormula(this.element.value))
      } catch {
        return ''
      }
    },
    classes() {
      return {
        [`element--alignment-horizontal-${this.element.alignment}`]: true,
        'element--no-value': !this.resolvedValue,
      }
    },
  },
}
</script>

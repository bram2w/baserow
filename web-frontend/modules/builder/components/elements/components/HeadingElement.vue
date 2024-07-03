<template>
  <div
    :class="{
      'element--no-value': !resolvedValue,
      [`element--alignment-horizontal-${element.alignment}`]: true,
    }"
  >
    <ABHeading :level="element.level" :style="getStyleOverride('typography')">
      {{ resolvedValue || $t('headingElement.noValue') }}
    </ABHeading>
  </div>
</template>

<script>
import element from '@baserow/modules/builder/mixins/element'
import { ensureString } from '@baserow/modules/core/utils/validator'

export default {
  name: 'HeadingElement',
  mixins: [element],
  props: {
    /**
     * @type {Object}
     * @property {number} level - The size of the heading
     * @property {string} value - The text displayed
     * @property {string} alignment - The alignment of the element on the page
     */
    element: {
      type: Object,
      required: true,
    },
  },
  computed: {
    resolvedValue() {
      return ensureString(this.resolveFormula(this.element.value))
    },
  },
}
</script>

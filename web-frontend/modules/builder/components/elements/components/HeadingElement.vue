<template>
  <div
    :class="{
      'element--no-value': !resolvedValue,
      [`element--alignment-horizontal-${element.alignment}`]: true,
    }"
  >
    <component
      :is="`h${element.level}`"
      class="heading-element__heading"
      :style="{
        '--color': resolveColor(element.font_color, headingColorVariables),
        '--font-size': `${
          builder.theme[`heading_${element.level}_font_size`]
        }px`,
      }"
    >
      {{ resolvedValue || $t('headingElement.noValue') }}
    </component>
  </div>
</template>

<script>
import element from '@baserow/modules/builder/mixins/element'
import headingElement from '@baserow/modules/builder/mixins/headingElement'

export default {
  name: 'HeadingElement',
  mixins: [element, headingElement],
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
      try {
        return this.resolveFormula(this.element.value)
      } catch (e) {
        return ''
      }
    },
  },
}
</script>

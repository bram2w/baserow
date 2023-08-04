<template>
  <component
    :is="`h${element.level}`"
    class="heading-element"
    :class="{ 'element--no-value': !resolvedValue }"
  >
    {{ resolvedValue || $t('headingElement.noValue') }}
  </component>
</template>

<script>
import element from '@baserow/modules/builder/mixins/element'

export default {
  name: 'HeadingElement',
  mixins: [element],
  props: {
    /**
     * @type {Object}
     * @property {number} level - The size of the heading
     * @property {string} value - The text displayed
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

<template>
  <component
    :is="`h${element.level}`"
    class="heading-element"
    :class="{ 'element--no-value': !element.value }"
  >
    {{ element.value || $t('headingElement.noValue') }}
  </component>
</template>

<script>
import textElement from '@baserow/modules/builder/mixins/elements/textElement'

export default {
  name: 'HeadingElement',
  mixins: [textElement],
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
}
</script>

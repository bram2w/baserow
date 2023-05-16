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
  name: 'HeaderElement',
  mixins: [textElement],
  props: {
    element: {
      type: Object,
      required: true,
    },
  },
}
</script>

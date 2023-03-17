<template>
  <component :is="`h${level}`">{{ value }}</component>
</template>

<script>
import textElement from '@baserow/modules/builder/mixins/elements/textElement'

export default {
  name: 'HeaderElement',
  mixins: [textElement],
  props: {
    level: {
      type: Number,
      required: true,
    },
  },
}
</script>

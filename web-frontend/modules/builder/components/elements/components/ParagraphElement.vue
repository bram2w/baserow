<template>
  <p>{{ value }}</p>
</template>

<script>
import textElement from '@baserow/modules/builder/mixins/elements/textElement'

export default {
  name: 'ParagraphElement',
  mixins: [textElement],
}
</script>

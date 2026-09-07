<template>
  <FormattedText :content="value" preset="block">
    <template #plain="{ text }">
      <span class="ab-text">{{ text }}</span>
    </template>
  </FormattedText>
</template>

<script>
import collectionField from '@baserow/modules/builder/mixins/collectionField'
import FormattedText from '@baserow/modules/builder/components/FormattedText'

export default {
  name: 'TextField',
  components: { FormattedText },
  mixins: [collectionField],
  props: {
    value: {
      type: String,
      required: true,
    },
  },
}
</script>

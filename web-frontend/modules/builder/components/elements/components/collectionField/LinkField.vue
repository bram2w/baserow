<template>
  <ABLink variant="button" :url="url" :target="target">
    {{ realLinkName }}
  </ABLink>
</template>

<script>
import collectionField from '@baserow/modules/builder/mixins/collectionField'

export default {
  name: 'LinkField',
  mixins: [collectionField],
  props: {
    url: {
      type: String,
      required: true,
    },
    linkName: {
      type: String,
      required: true,
    },
    target: {
      type: String,
      required: true,
    },
  },
  computed: {
    realLinkName() {
      if (this.linkName) {
        return this.linkName
      } else {
        return this.$t('linkField.details')
      }
    },
  },
}
</script>

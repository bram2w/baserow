<template>
  <div class="link-field">
    <ABLink variant="button" :url="url" :target="target">
      {{ realLinkName }}
    </ABLink>
  </div>
</template>

<script>
export default {
  name: 'LinkField',
  inject: ['mode', 'builder'],
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

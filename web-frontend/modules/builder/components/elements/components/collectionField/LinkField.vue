<template>
  <ABLink
    variant="button"
    v-bind="extraAttr"
    @click.prevent="onButtonFieldClick($event)"
  >
    {{ realLinkName }}
  </ABLink>
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
    isExternalLink: {
      type: Boolean,
      required: true,
    },
    navigationType: {
      type: String,
      required: true,
    },
    linkName: {
      type: String,
      required: true,
    },
  },
  computed: {
    extraAttr() {
      const attr = {}
      if (this.url) {
        attr.href = this.url
      }
      if (this.isExternalLink) {
        attr.rel = 'noopener noreferrer'
      }
      return attr
    },
    realLinkName() {
      if (this.linkName) {
        return this.linkName
      } else {
        return this.$t('linkField.details')
      }
    },
  },
  methods: {
    onButtonFieldClick(event) {
      if (this.mode === 'editing' || !this.url) {
        return
      }
      if (this.navigationType === 'custom') {
        window.location.href = this.url
      } else if (this.navigationType === 'page') {
        this.$router.push(this.url)
      }
    },
  },
}
</script>

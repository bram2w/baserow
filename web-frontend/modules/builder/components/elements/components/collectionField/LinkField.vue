<template>
  <a
    class="link-button-element-button"
    v-bind="extraAttr"
    @click="onButtonFieldClick($event)"
  >
    {{ realLinkName }}
  </a>
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
  },
  computed: {
    realUrl() {
      if (!this.url) {
        return ''
      }

      if (this.url.startsWith('/') && this.mode === 'preview') {
        return `/builder/${this.builder.id}/preview${this.url}`
      } else {
        return this.url
      }
    },
    isExternalLink() {
      return !this.realUrl.startsWith('/')
    },
    extraAttr() {
      const attr = {}
      if (this.realUrl) {
        attr.href = this.realUrl
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
      if (this.mode === 'editing') {
        event.preventDefault()
        return
      }

      if (!this.url) {
        event.preventDefault()
      } else if (!this.isExternalLink) {
        event.preventDefault()
        this.$router.push(this.realUrl)
      }
    },
  },
}
</script>

<template>
  <a
    class="link-button-element-button"
    v-bind="extraAttr"
    @click="onButtonFieldClick($event)"
  >
    {{ $t('linkField.details') }}
  </a>
</template>

<script>
export default {
  name: 'LinkField',
  inject: ['mode', 'builder'],
  props: {
    value: {
      type: String,
      required: true,
    },
  },
  computed: {
    url() {
      if (!this.value) {
        return ''
      }

      if (this.value.startsWith('/') && this.mode === 'preview') {
        return `/builder/${this.builder.id}/preview${this.value}`
      } else {
        return this.value
      }
    },
    isExternalLink() {
      return !this.url.startsWith('/')
    },
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
  },
  methods: {
    toUrl(url) {
      if (url.startsWith('/') && this.mode === 'preview') {
        return `/builder/${this.builder.id}/preview${url}`
      } else {
        return url
      }
    },
    onButtonFieldClick(event) {
      if (this.mode === 'editing') {
        event.preventDefault()
        return
      }

      if (!this.url) {
        event.preventDefault()
      } else if (!this.isExternalLink) {
        event.preventDefault()
        this.$router.push(this.url)
      }
    },
  },
}
</script>

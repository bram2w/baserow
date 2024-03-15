<template functional>
  <!-- must be in sync with `modules/core/components/Logo.vue` apart from the label. -->
  <div class="logo">
    <div v-if="$options.methods.showLabel(parent)" class="logo__label">
      by Baserow
    </div>
    <img
      :src="$options.methods.getLogoUrl(parent)"
      v-bind="props"
      :class="[data.staticClass, data.class]"
    />
  </div>
</template>

<script>
export default {
  name: 'EnterpriseLogo',
  methods: {
    showLabel(parent) {
      const settings = parent.$store.getters['settings/get']
      return !!settings.co_branding_logo
    },
    getLogoUrl(parent) {
      const baserowLogo = require('@baserow/modules/core/static/img/logo.svg')
      const settings = parent.$store.getters['settings/get']
      if (settings.co_branding_logo) {
        return settings.co_branding_logo.url
      }
      return baserowLogo
    },
  },
}
</script>

<template functional>
  <component
    :is="$options.methods.getComponent(parent)"
    v-if="$options.methods.getComponent(parent) !== null"
    v-bind="props"
    :class="[data.staticClass, data.class]"
  />
  <!-- must be in sync with modules/baserow_enterprise/components/EnterpriseLogo.vue -->
  <div v-else class="logo">
    <img
      src="@baserow/modules/core/static/img/logo.svg"
      v-bind="props"
      :class="[data.staticClass, data.class]"
    />
  </div>
</template>

<script>
export default {
  name: 'Logo',
  methods: {
    getComponent(parent) {
      return (
        Object.values(parent.$registry.getAll('plugin'))
          .filter((plugin) => plugin.getLogoComponent() !== null)
          .sort(
            (p1, p2) => p2.getLogoComponentOrder() - p1.getLogoComponentOrder()
          )
          .map((plugin) => plugin.getLogoComponent())[0] || null
      )
    },
  },
}
</script>

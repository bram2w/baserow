<template>
  <div class="theme_settings">
    <component
      :is="themeConfigBlock.component"
      v-for="themeConfigBlock in themeConfigBlocks"
      :key="themeConfigBlock.type"
      :builder="builder"
    />
  </div>
</template>

<script>
export default {
  name: 'ThemeSettings',
  props: {
    builder: {
      type: Object,
      required: true,
    },
  },
  computed: {
    themeConfigBlocks() {
      return Object.values(this.$registry.getAll('themeConfigBlock'))
    },
  },
}
</script>

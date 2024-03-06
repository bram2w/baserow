<template>
  <div :style="style" @click.self="$emit('click', $event)">
    <slot></slot>
  </div>
</template>

<script>
export default {
  name: 'ThemeProvider',
  inject: ['builder'],
  computed: {
    style() {
      const colors = {
        '--primary-color': this.builder.theme.primary_color,
        '--secondary-color': this.builder.theme.secondary_color,
      }
      const buttonColors = {
        '--button-color': this.builder.theme.primary_color,
      }
      const headings = Array.from([1, 2, 3, 4, 5, 6]).reduce(
        (headings, level) => ({
          [`--heading-h${level}--font-size`]: `${
            this.builder.theme[`heading_${level}_font_size`]
          }px`,
          [`--heading-h${level}--color`]:
            this.builder.theme[`heading_${level}_color`],
          ...headings,
        }),
        {}
      )
      return { ...colors, ...headings, ...buttonColors }
    },
  },
}
</script>
